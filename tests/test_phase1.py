"""Small dependency-light checks for Phase 1 analysis helpers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_engine.viral_detector import rank_transcript_segments
from face_tracker import build_crop_expressions


def test_transcript_ranker_returns_high_value_non_overlapping_clips():
    segments = [
        {"start": 0, "end": 5, "text": "Today I will tell you the biggest mistake people make."},
        {"start": 5, "end": 11, "text": "Why does this happen? Because they never understand the real reason!"},
        {"start": 11, "end": 18, "text": "Here is the simple solution and an important lesson."},
        {"start": 40, "end": 46, "text": "This is a completely different story about travel."},
        {"start": 46, "end": 55, "text": "Imagine how amazing this place looks at sunset!"},
    ]
    ranked = rank_transcript_segments(segments, target_duration=15, max_clips=3)
    assert ranked
    assert ranked[0]["score"] > 0
    assert "completeness" in ranked[0]["factors"]
    assert "coherence" in ranked[0]["factors"]
    assert ranked[0]["reason"]
    assert all(ranked[i]["end"] <= ranked[i + 1]["start"] or
               ranked[i]["start"] >= ranked[i + 1]["end"]
               for i in range(len(ranked) - 1))


def test_context_ranker_uses_whisper_quality_and_complete_thought():
    complete = [
        {"start": 0, "end": 5, "text": "Here is the truth about this important problem."},
        {"start": 5, "end": 12, "text": "The solution is simple, and it can change your life!"},
        {"start": 12, "end": 18, "text": "Remember this lesson before you make that mistake."},
    ]
    fragment = [
        {"start": 0, "end": 5, "text": "And because"},
        {"start": 5, "end": 12, "text": "it is actually a very important thing and"},
        {"start": 12, "end": 18, "text": "but then"},
    ]
    good = rank_transcript_segments(complete, target_duration=18, max_clips=1, min_duration=8)
    weak = rank_transcript_segments(fragment, target_duration=18, max_clips=1, min_duration=8)
    assert good and weak
    assert good[0]["factors"]["completeness"] > weak[0]["factors"]["completeness"]

    high_confidence = [
        {"start": 0, "end": 5, "text": "This is the real reason and the best solution.",
         "avg_logprob": -0.1, "no_speech_prob": 0.01},
        {"start": 5, "end": 12, "text": "You should remember this important lesson!",
         "avg_logprob": -0.1, "no_speech_prob": 0.01},
    ]
    low_confidence = [
        {"start": 0, "end": 5, "text": "This is the real reason and the best solution.",
         "avg_logprob": -1.2, "no_speech_prob": 0.8},
        {"start": 5, "end": 12, "text": "You should remember this important lesson!",
         "avg_logprob": -1.2, "no_speech_prob": 0.8},
    ]
    high = rank_transcript_segments(high_confidence, target_duration=12, max_clips=1, min_duration=8)
    low = rank_transcript_segments(low_confidence, target_duration=12, max_clips=1, min_duration=8)
    assert high and low
    assert high[0]["factors"]["speech_quality"] > low[0]["factors"]["speech_quality"]


def test_face_crop_expression_is_smooth_and_clamped():
    x, y = build_crop_expressions(
        [(0.0, 500.0, 300.0), (1.0, 520.0, 310.0)],
        "min(iw\\,ih*9/16)", "min(ih\\,iw*16/9)", 1920, 1080
    )
    assert "if(lt(t" in x
    assert "clip(" in x and "clip(" in y
    assert "iw-" in x and "ih-" in y


if __name__ == "__main__":
    test_transcript_ranker_returns_high_value_non_overlapping_clips()
    test_context_ranker_uses_whisper_quality_and_complete_thought()
    test_face_crop_expression_is_smooth_and_clamped()
    print("Phase 1 + Phase 2 helper tests passed.")
