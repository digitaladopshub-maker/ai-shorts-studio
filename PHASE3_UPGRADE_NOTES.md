# Phase 3 Upgrade Notes

## Included
- Reworked the uploaded-video preview layout: preview is shown first, with tracking status and fallback controls in a separate section underneath. The controls no longer share the preview's narrow side-by-side row, preventing them from covering the video.
- Increased the preview column's share of the main layout so portrait previews have more room.
- Added `multi_face_tracker.py`: samples multiple detected faces, maintains simple face tracks, measures changes in the lower-face/mouth region, and selects the face with the strongest visible mouth-motion signal when that signal is sufficiently distinct.
- Integrated this selection into portrait preview framing and final 9:16 clip rendering.
- If the visual speaker signal is ambiguous or faces are not detected, the system falls back to the longest/stablest face track, then to the existing Phase 1 centre/manual fallback.
- Existing Phase 1 and Phase 2 modules, subtitle engine, effects engine, and Live Streaming page are retained.

## Important limitations
- This is a free CPU-based visual activity estimate, not reliable audio-to-lip synchronization or guaranteed active-speaker identification. Camera cuts, side profiles, occlusion, low light, and multiple moving faces can confuse it.
- Uses OpenCV Haar frontal-face detection; profile-face detection and deep-learning identity tracking are not included.
- Streamlit Community Cloud CPU/RAM and temporary storage limits still apply. Long videos may take time or exceed free resource limits.
- Full Streamlit Cloud runtime testing must be performed after deployment; local syntax and helper tests do not guarantee cloud runtime behavior.

## Dependencies
No new package was added. NumPy is installed as an OpenCV dependency.

## Preview layout correction
- Moved Smart Face Tracking status, its explanation, and fallback sliders into a collapsed `Smart Framing Settings` expander in the right-hand settings column.
- The video preview column now contains only the preview image and its caption, preventing framing controls from crowding or visually overlapping the portrait preview.
- Automatic tracking remains enabled; the fallback sliders only adjust fallback crop positioning.
