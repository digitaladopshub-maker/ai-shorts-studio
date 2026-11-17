# AI Shorts Studio — Advanced Broadcast Upgrade

This project keeps the existing Clipping Studio and adds a live graphics compositor to the Live Streaming page.

## New live graphics features
- PNG/JPG/WEBP photo and logo overlays
- Multiple simultaneous layers
- Text overlays
- Lower-third banners
- Scrolling ticker
- Per-layer visibility and removal
- Position, width, opacity, font size, text and ticker speed editing
- Transparent graphics preview

## How it works
The Live Streaming page feeds a transparent RGBA overlay canvas into FFmpeg through a raw-video pipe. A background writer thread reads the latest overlay layer configuration and composites it with Pillow. Changes to the layer configuration are therefore reflected in the running stream without restarting FFmpeg.

The overlay canvas is 1280x720 and is scaled to the selected output resolution. Overlay refresh is 5 frames per second; the base stream remains 30 fps.

## Deploy
1. Replace the files in your GitHub repository with this project version.
2. Keep `requirements.txt` and `packages.txt` in the repository root.
3. Deploy/reboot the Streamlit app.
4. Start a live stream, then use the **Live Graphics & Overlay Studio** panel below the live controls.

No additional Python dependency is required; Pillow is already included in `requirements.txt`.

## Important limitations
- This is a server-side FFmpeg feature. The hosting environment must allow a long-running FFmpeg process and provide sufficient CPU/RAM/bandwidth.
- Streamlit Community Cloud can sleep, restart, or enforce resource limits; uninterrupted multi-hour streaming is not guaranteed there.
- Uploaded videos and overlay assets are stored on the app server's local disk and may be lost after a restart/redeploy.
- Keep the YouTube stream key private. Do not commit stream keys, cookies, `.env` files, or secrets to GitHub.
