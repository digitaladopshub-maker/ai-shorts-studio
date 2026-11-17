# AI Shorts Studio — Phase 1 Upgrade Notes

## Included

- Automatic face-aware 9:16 reframing; no manual face-tracking checkbox is required.
- OpenCV Haar face detection sampled through each clip, with subject association and smoothing.
- FFmpeg crop coordinates interpolated over clip time for less jumpy framing.
- Safe centre/manual-offset fallback when no face is detected.
- Portrait-safe crop dimensions so very tall or wide source footage does not request a crop larger than the source frame.
- Auto-Split AI now transcribes the source with local Whisper and ranks transcript windows using hook, question, emotion-word, context-length and duration-fit signals.
- Overlapping and near-duplicate candidate windows are filtered before export.
- The UI shows selected clip timestamps, transcript excerpts and a heuristic potential score.
- FFmpeg render failures are surfaced rather than silently adding a missing output to the gallery.

## Cost and network requirements

- No paid API, paid domain, paid hosting or new third-party runtime dependency was added.
- Uses the project's existing `openai-whisper`, `opencv-python-headless`, FFmpeg and Streamlit dependencies.
- Whisper's `base` model may need to be downloaded the first time the app runs in a fresh environment. Model download uses network bandwidth but does not require a paid API key.

## Important limitations in this phase

- The viral score is a transparent transcript heuristic, not a promise of virality and not yet a deep semantic LLM assessment.
- Face tracking currently follows the most plausible/large face between sampled frames. It does not yet identify the active speaker in a two-person conversation.
- Haar face detection can miss profile faces, occluded faces, low-light faces or very small faces; centre/manual fallback is used in those cases.
- Auto clipping falls back to evenly spaced timestamps if local Whisper cannot load or does not produce usable transcript windows.
- Streamlit Community Cloud has finite CPU/RAM and ephemeral local storage. Long videos and multiple simultaneous renders are not guaranteed on the free tier.

## Validation performed

- Python compilation passed for application modules and the new AI module.
- FFmpeg dynamic crop expression smoke test passed.
- Transcript ranking and crop-expression helper tests passed.
- Existing `app.py`, `streaming_page.py`, `effects_engine.py`, `subtitle_engine.py` and font assets were preserved.
