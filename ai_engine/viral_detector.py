"""Context-aware transcript ranking for free, local AI Shorts selection.

This is a transparent heuristic ranker, not an LLM and not a guarantee of virality.
It uses Whisper transcript text plus Whisper confidence/no-speech metadata when available.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

HOOK_TERMS = {
    "secret", "truth", "mistake", "why", "how", "never", "always", "shocking",
    "surprising", "important", "problem", "solution", "because", "actually",
    "imagine", "remember", "listen", "best", "worst", "reason", "lesson",
    "secretly", "galti", "sach", "kyun", "kaise", "lekin", "magar", "asal",
    "zindagi", "hairan", "sochiye", "yaad", "masla", "hal", "zaroori",
    "dekho", "sunno", "suno", "samjho", "waqai", "haqeeqat", "raaz",
    "here's", "here", "this", "what", "which", "everyone", "nobody",
}
EMOTION_TERMS = {
    "love", "fear", "angry", "anger", "happy", "sad", "excited", "amazing",
    "incredible", "beautiful", "crazy", "shocked", "funny", "laugh", "cry",
    "khushi", "ghussa", "dard", "mohabbat", "kamyaab", "pareshan", "zabardast",
    "hairan", "khauf", "dukh", "maza", "hansi", "kamal", "behtareen",
    "terrible", "wonderful", "dangerous", "powerful", "urgent",
}
QUESTION_WORDS = {
    "why", "how", "what", "who", "when", "where", "which", "kya", "kyun",
    "kaise", "kab", "kahan", "kon", "kis", "kaunsa",
}
WEAK_OPENERS = {
    "and", "but", "so", "because", "then", "although", "however",
    "aur", "lekin", "magar", "to", "phir", "kyunke", "qk", "matlab",
}
WEAK_ENDINGS = {
    "and", "but", "because", "or", "so", "to", "with", "if", "when",
    "aur", "lekin", "magar", "kyunke", "qk", "phir",
}
FILLERS = {
    "um", "uh", "erm", "hmm", "like", "basically", "actually", "you", "know",
    "matlab", "acha", "achha", "umm", "hmmm",
}


def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def _tokens(text):
    return [t.lower().strip("'") for t in re.findall(r"[\w']+", _clean(text), flags=re.UNICODE)]


def _word_count(text):
    return len(_tokens(text))


def _clamp(value):
    return max(0.0, min(100.0, float(value)))


def _score(text, duration, target_duration, segments=None):
    raw = _clean(text)
    words = _tokens(raw)
    if not words:
        return 0.0, {}

    token_set = set(words)
    hook_hits = len(token_set & HOOK_TERMS)
    emotion_hits = len(token_set & EMOTION_TERMS)
    question_hits = len(token_set & QUESTION_WORDS)

    hook = _clamp(28 + 14 * min(4, hook_hits) + (13 if "?" in raw[:120] else 0))
    emotion = _clamp(28 + 15 * min(4, emotion_hits) + (12 if "!" in raw else 0))
    question = 92 if "?" in raw else (68 if question_hits else 25)

    count = len(words)
    words_per_second = count / max(1.0, duration)
    density = _clamp(35 + min(1.0, words_per_second / 2.6) * 60)

    duration_fit = _clamp(100 - abs(duration - target_duration) /
                          max(1.0, target_duration) * 58)

    # Reward a clip that contains enough language to make sense on its own.
    context = _clamp(18 + min(1.0, count / 34.0) * 82)

    # Penalize clips that start/end on obvious fragments.
    starts_cleanly = words[0] not in WEAK_OPENERS
    ends_cleanly = words[-1] not in WEAK_ENDINGS
    punctuation_end = bool(re.search(r'[.!?…]["\')\]]*$', raw))
    completeness = 48 + (18 if starts_cleanly else -18) + (16 if ends_cleanly else -20)
    completeness += 18 if punctuation_end else 0
    completeness = _clamp(completeness)

    # A coherent short usually develops an idea rather than repeating the same words.
    unique_ratio = len(token_set) / max(1, count)
    repeated_ratio = sum(1 for a, b in zip(words, words[1:]) if a == b) / max(1, count - 1)
    coherence = _clamp(35 + min(1.0, unique_ratio / 0.72) * 55 - repeated_ratio * 45)

    # Whisper metadata: prefer speech-bearing, reasonably confident segments.
    quality_values = []
    if segments:
        for seg in segments:
            try:
                no_speech = float(seg.get("no_speech_prob", 0.0) or 0.0)
                logprob = float(seg.get("avg_logprob", -0.35) or -0.35)
                quality_values.append(_clamp(100 * (1.0 - no_speech) *
                                             max(0.25, min(1.0, (logprob + 1.5) / 1.5))))
            except (TypeError, ValueError):
                continue
    speech_quality = sum(quality_values) / len(quality_values) if quality_values else 70.0

    filler_count = sum(1 for w in words if w in FILLERS)
    filler_penalty = min(18, filler_count * 3)
    coherence = _clamp(coherence - filler_penalty)

    total = (
        0.17 * hook +
        0.12 * emotion +
        0.08 * question +
        0.10 * density +
        0.10 * duration_fit +
        0.13 * context +
        0.17 * completeness +
        0.08 * coherence +
        0.05 * speech_quality
    )
    factors = {
        "hook": round(hook),
        "emotion": round(emotion),
        "question": round(question),
        "density": round(density),
        "duration_fit": round(duration_fit),
        "context": round(context),
        "completeness": round(completeness),
        "coherence": round(coherence),
        "speech_quality": round(speech_quality),
    }
    return round(total, 1), factors


def _similar(a, b):
    aa = " ".join(_clean(a).lower().split())
    bb = " ".join(_clean(b).lower().split())
    if not aa or not bb:
        return 0.0
    return SequenceMatcher(None, aa, bb).ratio()


def rank_transcript_segments(segments, target_duration=30, max_clips=3, min_duration=8):
    """Return high-scoring, non-overlapping transcript windows.

    Whisper segment dictionaries may include avg_logprob and no_speech_prob.
    Clip boundaries follow transcript segment boundaries to reduce mid-sentence cuts.
    """
    usable = []
    for seg in segments or []:
        try:
            start, end = float(seg["start"]), float(seg["end"])
            text = _clean(seg.get("text", ""))
        except (KeyError, TypeError, ValueError):
            continue
        if end > start and text:
            usable.append({
                "start": start, "end": end, "text": text,
                "avg_logprob": seg.get("avg_logprob"),
                "no_speech_prob": seg.get("no_speech_prob"),
            })
    usable.sort(key=lambda s: (s["start"], s["end"]))
    if not usable or max_clips <= 0:
        return []

    candidates = []
    max_duration = max(float(min_duration), float(target_duration) * 1.25)
    for i in range(len(usable)):
        combined = []
        window_segments = []
        start = usable[i]["start"]
        end = start
        for j in range(i, len(usable)):
            # Avoid combining distant utterances into a misleading clip.
            if j > i and usable[j]["start"] - end > 2.8:
                break
            if j > i and usable[j]["end"] - start > max_duration:
                break
            combined.append(usable[j]["text"])
            window_segments.append(usable[j])
            end = max(end, usable[j]["end"])
            duration = end - start
            if min_duration <= duration <= max_duration:
                text = " ".join(combined)
                score, factors = _score(text, duration, target_duration, window_segments)
                candidates.append({
                    "start": max(0.0, start), "duration": duration, "end": end,
                    "text": text, "score": score, "factors": factors,
                    "reason": _reason(factors),
                })
            if duration >= target_duration:
                break

    candidates.sort(key=lambda c: (c["score"], c["duration"]), reverse=True)
    selected = []
    for item in candidates:
        if any(_similar(item["text"], chosen["text"]) > 0.78 or
               (item["start"] < chosen["end"] and item["end"] > chosen["start"])
               for chosen in selected):
            continue
        selected.append(item)
        if len(selected) >= int(max_clips):
            break
    return sorted(selected, key=lambda c: c["start"])


def _reason(factors):
    if not factors:
        return "Transcript signal kam hai"
    strengths = sorted(factors.items(), key=lambda pair: pair[1], reverse=True)
    names = {
        "hook": "strong hook", "emotion": "emotional language",
        "question": "question/curiosity", "density": "speech density",
        "duration_fit": "duration fit", "context": "enough context",
        "completeness": "complete thought", "coherence": "coherent wording",
        "speech_quality": "speech confidence",
    }
    return " • ".join(names.get(k, k) for k, v in strengths[:3] if v >= 65) or "Balanced transcript signals"
