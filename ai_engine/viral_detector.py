"""Transcript-driven short candidate ranking; no paid API or network calls."""
from __future__ import annotations
import re
from difflib import SequenceMatcher

HOOK_TERMS = {
    "secret", "truth", "mistake", "why", "how", "never", "always", "shocking",
    "surprising", "important", "problem", "solution", "because", "actually",
    "imagine", "remember", "listen", "best", "worst", "reason", "lesson",
    "secretly", "galti", "sach", "kyun", "kaise", "lekin", "magar", "asal",
    "zindagi", "hairan", "sochiye", "yaad", "masla", "hal", "zaroori",
}
EMOTION_TERMS = {
    "love", "fear", "angry", "anger", "happy", "sad", "excited", "amazing",
    "incredible", "beautiful", "crazy", "shocked", "funny", "laugh", "cry",
    "khushi", "ghussa", "dard", "mohabbat", "kamyaab", "pareshan", "zabardast",
    "hairan", "khauf", "dukh", "maza", "hansi",
}


def _clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def _word_count(text):
    return len(re.findall(r"[\w']+", text, flags=re.UNICODE))


def _score(text, duration, target_duration):
    words = _clean(text).lower().split()
    if not words:
        return 0.0, {}
    token_set = {re.sub(r"[^\w]", "", w) for w in words}
    hook = min(100, 35 + 13 * len(token_set & HOOK_TERMS) + (15 if "?" in text[:100] else 0))
    emotion = min(100, 30 + 16 * len(token_set & EMOTION_TERMS) + (12 if "!" in text else 0))
    question = 90 if "?" in text else (55 if any(w in token_set for w in {"why", "how", "what", "who", "when", "kyun", "kaise", "kya"}) else 25)
    density = min(100, int(45 + min(1.0, _word_count(text) / max(1, duration * 2.2)) * 45))
    duration_fit = max(0, 100 - int(abs(duration - target_duration) / max(1, target_duration) * 65))
    context = 85 if len(words) >= 18 else (60 if len(words) >= 9 else 25)
    total = 0.27 * hook + 0.22 * emotion + 0.12 * question + 0.15 * density + 0.10 * duration_fit + 0.14 * context
    return round(total, 1), {"hook": round(hook), "emotion": round(emotion), "question": round(question), "context": round(context)}


def _similar(a, b):
    aa = " ".join(_clean(a).lower().split())
    bb = " ".join(_clean(b).lower().split())
    if not aa or not bb:
        return 0.0
    return SequenceMatcher(None, aa, bb).ratio()


def rank_transcript_segments(segments, target_duration=30, max_clips=3, min_duration=8):
    """Rank overlapping transcript windows and return non-duplicate clip ranges.

    Input segments follow Whisper's {start, end, text} schema. Window boundaries
    follow transcript segment boundaries to reduce mid-sentence cuts.
    """
    usable = []
    for seg in segments or []:
        try:
            start, end = float(seg["start"]), float(seg["end"])
            text = _clean(seg.get("text", ""))
        except (KeyError, TypeError, ValueError):
            continue
        if end > start and text:
            usable.append({"start": start, "end": end, "text": text})
    if not usable:
        return []

    candidates = []
    for i in range(len(usable)):
        combined = []
        start = usable[i]["start"]
        end = start
        for j in range(i, len(usable)):
            if j > i and usable[j]["end"] - start > target_duration * 1.25:
                break
            combined.append(usable[j]["text"])
            end = usable[j]["end"]
            duration = end - start
            if duration >= min_duration and duration <= target_duration * 1.25:
                text = " ".join(combined)
                score, factors = _score(text, duration, target_duration)
                candidates.append({"start": max(0, start), "duration": duration,
                                   "end": end, "text": text, "score": score,
                                   "factors": factors})
            if duration >= target_duration:
                break

    candidates.sort(key=lambda c: c["score"], reverse=True)
    selected = []
    for item in candidates:
        if any(_similar(item["text"], chosen["text"]) > 0.78 or
               (item["start"] < chosen["end"] and item["end"] > chosen["start"])
               for chosen in selected):
            continue
        selected.append(item)
        if len(selected) >= max_clips:
            break
    return sorted(selected, key=lambda c: c["start"])

