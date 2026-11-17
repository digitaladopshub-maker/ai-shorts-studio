# Podcast Mode Update

- Added a Podcast Mode ON/OFF toggle inside the existing Clipping page.
- OFF uses the standard continuity-based face tracker.
- ON uses the existing multi-face visible-mouth-activity heuristic to estimate the likely active speaker and follow that face in vertical clips.
- Existing transcript-based viral selection, subtitles, effects, export, and Live Streaming code are unchanged.
- Advanced fallback framing remains available below the preview.

## Important limitation
This update does not implement audio speaker diarization or automatic split-screen. Mouth-region visual activity is only an estimate and can be confused by camera motion, lighting, or people moving. When confidence is weak, it falls back to regular face tracking. Split-screen needs a separate multi-person layout/render pipeline and is not claimed as completed here.

## Validation
- `clipping_page.py` compiles.
- Existing automated tests: 5 passed.
- Live Streamlit Cloud runtime and real multi-speaker footage have not been tested in this environment.
