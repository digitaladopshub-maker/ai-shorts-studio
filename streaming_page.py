
import os
import json
import time
import threading
import subprocess
import uuid
import urllib.request
import urllib.error
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
STREAM_DIR = BASE_DIR / "streaming_uploads"
ASSET_DIR = STREAM_DIR / "overlay_assets"
STATE_PATH = STREAM_DIR / "overlay_state.json"
STREAM_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720
OVERLAY_FPS = 5
LOG_PATH = STREAM_DIR / "ffmpeg_live.log"

PLATFORMS = {
    "YouTube": "rtmp://a.rtmp.youtube.com/live2",
    "Facebook": "rtmps://live-api-s.facebook.com:443/rtmp/",
    "TikTok": "",
    "Custom RTMP": "",
}

def _load_profiles():
    """Accounts are intentionally temporary: kept only in this Streamlit session."""
    return st.session_state.setdefault("stream_profiles_session", [])


def _save_profiles(profiles):
    """Update in-memory accounts only; nothing is written to disk or saved for next visit."""
    st.session_state["stream_profiles_session"] = profiles


def _tee_escape(value):
    # FFmpeg tee URL option escaping. RTMP keys normally contain URL-safe characters.
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def _alive(proc):
    return proc is not None and proc.poll() is None


def _resolve_video_url(source_url):
    """Resolve a supported page URL and return its matching media request headers."""
    source_url = (source_url or "").strip()
    if not source_url.lower().startswith(("http://", "https://")):
        raise ValueError("Enter a valid http:// or https:// video page URL.")

    from yt_dlp import YoutubeDL

    options = {
        "format": (
            "best[protocol^=http][vcodec!=none][acodec!=none]/"
            "best[protocol^=m3u8][vcodec!=none][acodec!=none]/"
            "best[vcodec!=none][acodec!=none]/best"
        ),
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "skip_download": True, "extract_flat": False,
        "socket_timeout": 30, "retries": 3, "extractor_retries": 3,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(source_url, download=False)
    if info and info.get("entries"):
        info = next((entry for entry in info["entries"] if entry), None)
    if not info:
        raise ValueError("No video information was returned for this URL.")

    # yt-dlp may expose the selected media URL at the top level while the
    # browser-like request headers live on the selected format. Match them
    # by URL rather than assuming info['http_headers'] is always sufficient.
    media_url = info.get("url")
    headers = {}
    selected_format = None
    requested_formats = info.get("requested_formats") or []
    all_formats = requested_formats + (info.get("formats") or [])
    if media_url:
        selected_format = next(
            (fmt for fmt in all_formats if fmt.get("url") == media_url), None
        )
    headers.update(info.get("http_headers") or {})
    if selected_format:
        headers.update(selected_format.get("http_headers") or {})

    if not media_url:
        formats = [fmt for fmt in (info.get("formats") or [])
                   if fmt.get("url") and fmt.get("vcodec") != "none"
                   and fmt.get("acodec") != "none"]
        if formats:
            formats.sort(key=lambda fmt: (
                fmt.get("protocol", "").startswith(("http", "m3u8")),
                fmt.get("height") or 0,
                fmt.get("tbr") or 0,
            ))
            selected_format = formats[-1]
            media_url = selected_format["url"]
            headers = dict(info.get("http_headers") or {})
            headers.update(selected_format.get("http_headers") or {})

    if not media_url:
        raise ValueError(
            "Could not resolve a direct audio/video stream. The link may be private, "
            "login-protected, live-only, or unsupported."
        )

    # Keep the same browser-like request context for the probe and FFmpeg.
    # Preserve extractor-provided values; only fill missing common headers.
    headers.setdefault("User-Agent", (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ))
    headers.setdefault("Accept", "*/*")
    headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    headers.setdefault("Referer", source_url)
    return media_url, headers


def _probe_media_url(media_url, headers=None, timeout=20):
    """Verify that the resolved media URL is currently readable without downloading it."""
    request_headers = dict(headers or {})
    request_headers["Range"] = "bytes=0-0"
    request = urllib.request.Request(media_url, headers=request_headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            if status not in (200, 206):
                raise ValueError(f"Media server returned HTTP {status} during the playback check.")
            response.read(1)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise ValueError(
                "The media server returned HTTP 403 during the playback check. "
                "The link may be expired or require a matching login/session. Fetch the URL again."
            ) from exc
        raise ValueError(f"Media playback check failed with HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not reach the media server during the playback check: {exc.reason}") from exc
    return True


def _format_ffmpeg_headers(headers):
    """Convert yt-dlp request headers to FFmpeg's required CRLF format."""
    return "".join(f"{key}: {value}\r\n" for key, value in (headers or {}).items())


def _load_layers():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save_layers(layers):
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(layers, f, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)


def _font(size, bold=False):
    candidates = [
        BASE_DIR / "fonts" / ("Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _rgba(hex_color, alpha=255):
    value = (hex_color or "#FFFFFF").lstrip("#")
    try:
        rgb = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
        return (*rgb, int(alpha))
    except Exception:
        return (255, 255, 255, int(alpha))


def _compose_overlay(layers):
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    now = time.time()
    for layer in layers:
        if not layer.get("visible", True):
            continue
        kind = layer.get("type")
        x = int(layer.get("x", 40))
        y = int(layer.get("y", 40))
        try:
            if kind == "photo":
                path = Path(layer.get("path", ""))
                if not path.exists():
                    continue
                with Image.open(path) as source:
                    image = source.convert("RGBA")
                max_w = max(20, min(900, int(layer.get("width", 260))))
                max_h = max(20, min(600, int(layer.get("height", 180))))
                image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                opacity = max(0, min(100, int(layer.get("opacity", 100))))
                if opacity < 100:
                    alpha = image.getchannel("A").point(lambda p: int(p * opacity / 100))
                    image.putalpha(alpha)
                canvas.alpha_composite(image, (x, y))

            elif kind in ("text", "banner", "ticker"):
                draw = ImageDraw.Draw(canvas)
                text = str(layer.get("text", ""))[:500]
                size = max(12, min(100, int(layer.get("font_size", 36))))
                font = _font(size, bold=True)
                color = _rgba(layer.get("color", "#FFFFFF"))
                if kind == "ticker":
                    # Smooth left-to-right repeat across the bottom ticker area.
                    box_h = max(48, size + 28)
                    draw.rectangle((0, CANVAS_H-box_h, CANVAS_W, CANVAS_H), fill=_rgba(layer.get("background", "#111827"), 235))
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_w = max(1, bbox[2] - bbox[0])
                    travel = CANVAS_W + text_w
                    tx = CANVAS_W - int((now * max(40, int(layer.get("speed", 100)))) % travel)
                    draw.text((tx, CANVAS_H-box_h + (box_h-size)//2 - bbox[1]), text, font=font, fill=color)
                elif kind == "banner":
                    pad_x, pad_y = 22, 14
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                    box_w = min(CANVAS_W-x, tw + pad_x*2)
                    box_h = th + pad_y*2
                    bg = _rgba(layer.get("background", "#111827"), int(layer.get("background_opacity", 230)))
                    draw.rounded_rectangle((x, y, x+box_w, y+box_h), radius=12, fill=bg)
                    draw.text((x+pad_x, y+pad_y-bbox[1]), text, font=font, fill=color)
                else:
                    draw.text((x, y), text, font=font, fill=color)
        except Exception:
            # A malformed/removed layer must not terminate the live stream.
            continue
    return canvas


def _overlay_writer(proc, stop_event):
    """Feed complete transparent RGBA frames to FFmpeg, even when pipe writes are partial."""
    frame_bytes = CANVAS_W * CANVAS_H * 4
    interval = 1.0 / OVERLAY_FPS
    try:
        while not stop_event.is_set() and proc.poll() is None:
            started = time.time()
            frame = _compose_overlay(_load_layers())
            raw = frame.tobytes()
            if len(raw) != frame_bytes:
                raise ValueError(f"Overlay frame size mismatch: {len(raw)} != {frame_bytes}")
            # Unbuffered pipe writes can be partial for frames larger than PIPE_BUF.
            # Write the entire frame before sending the next one or rawvideo becomes misaligned.
            view = memoryview(raw)
            while view and not stop_event.is_set() and proc.poll() is None:
                written = proc.stdin.write(view)
                if written is None or written <= 0:
                    raise BrokenPipeError("FFmpeg overlay input pipe closed")
                view = view[written:]
            delay = interval - (time.time() - started)
            if delay > 0:
                stop_event.wait(delay)
    except (BrokenPipeError, OSError, ValueError) as exc:
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as log:
                log.write(f"\n[overlay writer] {type(exc).__name__}: {exc}\n")
        except OSError:
            pass
    finally:
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        except Exception:
            pass


def _stderr_reader(proc):
    """Drain FFmpeg stderr so diagnostics are retained and the stderr pipe cannot fill."""
    if proc.stderr is None:
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log:
            for raw_line in iter(proc.stderr.readline, b""):
                try:
                    log.write(raw_line.decode("utf-8", errors="replace"))
                    log.flush()
                except Exception:
                    continue
    except OSError:
        pass


def _stop_stream():
    proc = st.session_state.get("stream_process")
    event = st.session_state.get("overlay_stop_event")
    if event:
        event.set()
    if _alive(proc):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    st.session_state.stream_process = None
    st.session_state.overlay_thread = None
    st.session_state.overlay_stop_event = None


def _add_layer(layer):
    layers = _load_layers()
    layer["id"] = uuid.uuid4().hex[:8]
    layer["visible"] = True
    layers.append(layer)
    _save_layers(layers)


def _render_graphics_studio():
    st.markdown("---")
    st.header("🎨 Live Graphics & Overlay Studio")
    st.caption("Graphics added here appear as overlays on the running stream. Changes apply live without restarting the stream.")
    layers = _load_layers()

    with st.expander("🖼️ Add Photo / Logo", expanded=False):
        photo = st.file_uploader("PNG / JPG / WEBP image", type=["png", "jpg", "jpeg", "webp"], key="overlay_photo")
        c1, c2, c3 = st.columns(3)
        px = c1.number_input("X position", 0, CANVAS_W-1, 40, key="photo_x")
        py = c2.number_input("Y position", 0, CANVAS_H-1, 40, key="photo_y")
        pw = c3.slider("Width", 40, 900, 260, key="photo_width")
        opacity = st.slider("Photo opacity", 10, 100, 100, key="photo_opacity")
        if st.button("＋ Add Photo / Logo", key="add_photo"):
            if photo is None:
                st.warning("Upload an image first.")
            else:
                ext = Path(photo.name).suffix.lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                    st.error("Unsupported image format.")
                else:
                    asset_path = ASSET_DIR / f"{uuid.uuid4().hex}{ext}"
                    asset_path.write_bytes(photo.getbuffer())
                    _add_layer({"type":"photo","name":photo.name,"path":str(asset_path),"x":int(px),"y":int(py),"width":int(pw),"height":600,"opacity":int(opacity)})
                    st.success("Photo/logo added to live graphics.")
                    st.rerun()

    with st.expander("✍️ Add Text", expanded=False):
        txt = st.text_input("Text", max_chars=180, key="overlay_text")
        c1, c2, c3 = st.columns(3)
        tx = c1.number_input("X", 0, CANVAS_W-1, 60, key="text_x")
        ty = c2.number_input("Y", 0, CANVAS_H-1, 60, key="text_y")
        fs = c3.slider("Font size", 14, 90, 36, key="text_size")
        color = st.color_picker("Text color", "#FFFFFF", key="text_color")
        if st.button("＋ Add Text", key="add_text"):
            if txt.strip():
                _add_layer({"type":"text","name":txt[:32],"text":txt,"x":int(tx),"y":int(ty),"font_size":int(fs),"color":color})
                st.success("Text added to the live stream.")
                st.rerun()
            else:
                st.warning("Enter text.")

    with st.expander("📢 Add Banner / Lower Third", expanded=False):
        banner_text = st.text_input("Banner text", max_chars=180, key="banner_text")
        c1, c2, c3 = st.columns(3)
        bx = c1.number_input("Banner X", 0, CANVAS_W-1, 40, key="banner_x")
        by = c2.number_input("Banner Y", 0, CANVAS_H-1, 520, key="banner_y")
        bfs = c3.slider("Banner font size", 14, 64, 30, key="banner_size")
        bc = st.color_picker("Banner text color", "#FFFFFF", key="banner_color")
        bg = st.color_picker("Banner background", "#B91C1C", key="banner_bg")
        if st.button("＋ Add Banner", key="add_banner"):
            if banner_text.strip():
                _add_layer({"type":"banner","name":banner_text[:32],"text":banner_text,"x":int(bx),"y":int(by),"font_size":int(bfs),"color":bc,"background":bg,"background_opacity":230})
                st.success("Banner added to the live stream.")
                st.rerun()
            else:
                st.warning("Enter banner text.")

    with st.expander("📜 Add Scrolling Ticker", expanded=False):
        ticker_text = st.text_input("Ticker announcement", max_chars=250, key="ticker_text")
        c1, c2, c3 = st.columns(3)
        tfs = c1.slider("Ticker font size", 16, 54, 28, key="ticker_size")
        tc = c2.color_picker("Ticker text color", "#FFFFFF", key="ticker_color")
        tb = c3.color_picker("Ticker background", "#111827", key="ticker_bg")
        speed = st.slider("Ticker speed", 40, 240, 100, key="ticker_speed")
        if st.button("＋ Add Scrolling Ticker", key="add_ticker"):
            if ticker_text.strip():
                _add_layer({"type":"ticker","name":ticker_text[:32],"text":ticker_text,"font_size":int(tfs),"color":tc,"background":tb,"speed":int(speed)})
                st.success("Scrolling ticker added to the live stream.")
                st.rerun()
            else:
                st.warning("Enter ticker text.")

    st.markdown("**Active graphics layers**")
    if not layers:
        st.info("No overlays yet. Add a photo, text, banner, or ticker above.")
    for layer in layers:
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 2, 2])
            c1.write(f"**{layer.get('type','layer').title()}** · {layer.get('name','')}")
            visible = c2.checkbox("Visible", value=bool(layer.get("visible", True)), key=f"vis_{layer['id']}")
            if visible != bool(layer.get("visible", True)):
                layer["visible"] = visible
                _save_layers(layers)
            if c3.button("Remove", key=f"remove_{layer['id']}"):
                if layer.get("type") == "photo":
                    try:
                        Path(layer.get("path","")).unlink(missing_ok=True)
                    except Exception:
                        pass
                layers = [item for item in _load_layers() if item.get("id") != layer["id"]]
                _save_layers(layers)
                st.rerun()

            with st.expander("Edit position / style", expanded=False):
                with st.form(f"edit_layer_{layer['id']}"):
                    e1, e2, e3 = st.columns(3)
                    ex = e1.number_input("X", 0, CANVAS_W-1, int(layer.get("x", 40)), key=f"edit_x_{layer['id']}")
                    ey = e2.number_input("Y", 0, CANVAS_H-1, int(layer.get("y", 40)), key=f"edit_y_{layer['id']}")
                    if layer.get("type") == "photo":
                        ew = e3.slider("Width", 40, 900, max(40, min(900, int(layer.get("width", 260)))), key=f"edit_w_{layer['id']}")
                        eo = st.slider("Opacity", 10, 100, max(10, min(100, int(layer.get("opacity", 100)))), key=f"edit_o_{layer['id']}")
                    elif layer.get("type") == "ticker":
                        ew = e3.slider("Scroll speed", 40, 240, max(40, min(240, int(layer.get("speed", 100)))), key=f"edit_speed_{layer['id']}")
                        eo = st.slider("Font size", 16, 54, max(16, min(54, int(layer.get("font_size", 28)))), key=f"edit_fs_{layer['id']}")
                    else:
                        ew = e3.slider("Font size", 14, 90, max(14, min(90, int(layer.get("font_size", 36)))), key=f"edit_fs_{layer['id']}")
                        eo = None
                    new_text = None
                    if layer.get("type") in ("text", "banner", "ticker"):
                        new_text = st.text_input("Text", value=layer.get("text", ""), key=f"edit_text_{layer['id']}")
                    if st.form_submit_button("Apply changes"):
                        layer["x"], layer["y"] = int(ex), int(ey)
                        if layer.get("type") == "photo":
                            layer["width"], layer["opacity"] = int(ew), int(eo)
                        elif layer.get("type") == "ticker":
                            layer["speed"], layer["font_size"] = int(ew), int(eo)
                        else:
                            layer["font_size"] = int(ew)
                        if new_text is not None:
                            layer["text"] = new_text
                            layer["name"] = new_text[:32]
                        _save_layers(layers)
                        st.success("Changes applied to the live stream.")
                        st.rerun()
    if layers and st.button("Clear all graphics", key="clear_all_graphics"):
        for layer in layers:
            if layer.get("type") == "photo":
                try:
                    Path(layer.get("path","")).unlink(missing_ok=True)
                except Exception:
                    pass
        _save_layers([])
        st.rerun()
    st.caption("Overlay canvas: 1280×720 with a transparent background. Set the position and width when adding a photo/logo.")
    writer = st.session_state.get("overlay_thread")
    if writer is not None and not writer.is_alive():
        st.error("Overlay sender thread stopped. Check the FFmpeg log below.")
    st.markdown("**Graphics preview**")
    st.image(_compose_overlay(_load_layers()), caption="Transparent overlay preview (actual video ke upar composite hota hai)", use_container_width=True)


def _render_account_manager():
    """Clean session-only destination cards with editable platform ingest URLs."""
    st.subheader("Streaming Platforms")
    slots_key = "stream_destination_slots"
    if slots_key not in st.session_state:
        st.session_state[slots_key] = [{"id": "slot_1", "platform": "YouTube", "key": "", "active": False}]

    slots = st.session_state[slots_key]
    active_profiles = []
    for index, slot in enumerate(slots):
        sid = slot["id"]
        old_platform = slot.get("platform", "YouTube")
        platform_options = list(PLATFORMS)
        with st.container(border=True):
            top_left, top_right = st.columns([3.2, 1])
            platform = top_left.selectbox(
                f"Platform {index + 1}", platform_options,
                index=platform_options.index(old_platform) if old_platform in platform_options else 0,
                key=f"dest_platform_{sid}"
            )
            active = top_right.toggle("Send to this platform", value=bool(slot.get("active", False)), key=f"dest_active_{sid}")

            # A changed destination must not accidentally reuse the previous platform's key.
            if platform != old_platform:
                st.session_state[f"dest_key_{sid}"] = ""
                st.session_state[f"dest_server_{sid}"] = PLATFORMS.get(platform, "")
                slot["key"] = ""

            default_server = PLATFORMS.get(platform, "")
            if platform == old_platform:
                server_value = slot.get("server") or default_server
            else:
                server_value = default_server

            if platform in ("Facebook", "TikTok", "Custom RTMP"):
                server = st.text_input(
                    "Server URL", value=server_value,
                    placeholder="Paste the URL from Facebook Live Producer" if platform == "Facebook" else "rtmp:// or rtmps:// server URL",
                    key=f"dest_server_{sid}"
                )
                if platform == "Facebook":
                    st.caption("Use the exact Server URL from Live Producer. On Facebook, click Go Live after the preview appears.")
                elif platform == "TikTok":
                    st.caption("Paste the RTMP URL provided by your TikTok LIVE Center.")
            else:
                server = default_server

            stream_key = st.text_input(
                "Stream Key", value=slot.get("key", ""), type="password",
                placeholder="Paste your stream key here", key=f"dest_key_{sid}"
            )
            slot.update({"platform": platform, "key": stream_key, "active": active, "server": server})

            if active:
                if stream_key.strip() and server.strip().startswith(("rtmp://", "rtmps://")):
                    active_profiles.append({
                        "id": sid, "name": f"{platform} {index + 1}", "platform": platform,
                        "server": server.strip(), "key": stream_key.strip()
                    })
                else:
                    st.warning("Enter a valid Server URL and Stream Key to enable this platform.")

    # Show a fresh empty card after the last destination is activated and configured.
    if slots and slots[-1].get("active") and slots[-1].get("key", "").strip() and slots[-1].get("server", "").strip().startswith(("rtmp://", "rtmps://")):
        slots.append({"id": f"slot_{uuid.uuid4().hex[:8]}", "platform": "YouTube", "key": "", "active": False})
    st.session_state[slots_key] = slots
    _save_profiles(active_profiles)

    left, center, right = st.columns([1, 1.4, 1])
    with center:
        if st.button("＋ Add Platform", key="add_destination_slot", use_container_width=True):
            slots.append({"id": f"slot_{uuid.uuid4().hex[:8]}", "platform": "YouTube", "key": "", "active": False})
            st.session_state[slots_key] = slots
            st.rerun()


def render_streaming_page():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
    .stApp, [data-testid="stAppViewContainer"] { background: #080b12; color: #f4f7fb; }
    [data-testid="stHeader"] { background: rgba(8,11,18,0.96); }
    [data-testid="stSidebar"] { background: #05070c; }
    [data-testid="stVerticalBlockBorderWrapper"] > div { background: linear-gradient(145deg,#111a29,#0d1420); border: 1px solid #2b3a50; border-radius: 16px; }
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
    [data-testid="stMarkdownContainer"] p, .stCaption, label { color: #e2e8f0 !important; }
    [data-testid="stWidgetLabel"] p { font-weight: 600 !important; font-size: .92rem !important; }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stDateInput"] input, div[data-testid="stTimeInput"] input {
        background: #111c2c !important; color: #f8fafc !important; border-color: #40516b !important; border-radius: 10px !important;
        -webkit-text-fill-color: #f8fafc !important;
    }
    div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] { background: #111c2c !important; color: #f8fafc !important; }
    div[data-baseweb="popover"] li:hover { background: #26364d !important; }
    textarea::placeholder, input::placeholder { color: #a8b6c9 !important; opacity: 1 !important; }
    [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus { border-color: #60a5fa !important; box-shadow: 0 0 0 1px #60a5fa !important; }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within { border-color: #60a5fa !important; box-shadow: 0 0 0 1px #60a5fa !important; }
    div.stButton > button { border-radius: 11px; min-height: 2.6rem; font-weight: 650; border: 1px solid #3b82f6; background: #1d4ed8; color: #fff; padding: .45rem 1.2rem; }
    div.stButton > button:hover { background: #2563eb; border-color: #60a5fa; color: #fff; }
    div[data-testid="stToggle"] label { color: #e2e8f0 !important; font-weight: 600; }
    h1, h2, h3 { color: #f8fafc !important; letter-spacing: -.025em; }
    </style>""", unsafe_allow_html=True)
    st.title("📡 Live Streaming Studio")
    _render_account_manager()
    st.markdown("---")
    proc = st.session_state.get("stream_process")
    running = _alive(proc)

    if running:
        st.success("The FFmpeg streaming process is running.")
        active = st.session_state.get("active_destinations", [])
        st.write("**Active destinations:** " + (", ".join(active) if active else "Unknown"))
        if st.button("⏹ Stop Streaming", type="primary", use_container_width=True):
            _stop_stream()
            st.session_state.active_destinations = []
            st.rerun()
    else:
        source_mode = st.radio("Video Source", ["Upload Video", "Video URL"], horizontal=True, key="stream_source_mode")
        uploaded = None
        video_url = ""
        if source_mode == "Upload Video":
            uploaded = st.file_uploader("Upload an MP4 video", type=["mp4"], key="stream_video")
        else:
            video_url = st.text_input("Video URL (YouTube / Facebook / TikTok)", placeholder="https://...", key="stream_video_url")
            st.caption("Public video URLs are resolved to a direct media stream. The video file is not downloaded or saved.")
            fetch_col, _status_col = st.columns([1, 2])
            with fetch_col:
                fetch_clicked = st.button("🔎 Fetch / Check Video", key="fetch_video_url", use_container_width=True)
            if fetch_clicked:
                st.session_state.pop("resolved_video_source", None)
                st.session_state.pop("resolved_video_url", None)
                st.session_state.pop("resolved_video_headers", None)
                if not video_url.strip():
                    st.session_state["video_fetch_error"] = "Enter a video URL before fetching."
                    st.session_state["video_fetch_error_source"] = video_url.strip()
                    st.session_state.pop("video_fetch_success", None)
                else:
                    with st.spinner("Checking the video URL and resolving its media stream..."):
                        try:
                            resolved_url, resolved_headers = _resolve_video_url(video_url)
                            _probe_media_url(resolved_url, resolved_headers)
                            st.session_state["resolved_video_source"] = video_url.strip()
                            st.session_state["resolved_video_url"] = resolved_url
                            st.session_state["resolved_video_headers"] = resolved_headers
                            st.session_state["video_fetch_success"] = True
                            st.session_state.pop("video_fetch_error", None)
                        except Exception as exc:
                            st.session_state["video_fetch_success"] = False
                            st.session_state["video_fetch_error_source"] = video_url.strip()
                            st.session_state["video_fetch_error"] = f"{type(exc).__name__}: {exc}"
            if st.session_state.get("resolved_video_source") == video_url.strip() and st.session_state.get("video_fetch_success"):
                st.success("Video fetched successfully — Ready to Live. You can now click Start Multi-Platform Live.")
            elif (st.session_state.get("video_fetch_error")
                  and st.session_state.get("video_fetch_error_source") == video_url.strip()):
                st.error("Video fetch failed: " + st.session_state["video_fetch_error"])
            else:
                st.info("Video not checked yet. Click Fetch / Check Video before starting the live stream.")
        profiles = _load_profiles()
        hours = st.number_input("Stream duration (hours)", min_value=1, max_value=12, value=4, step=1)
        quality = st.selectbox("Output quality", ["1080p", "720p", "480p"])
        profiles_quality = {"1080p": ("1920:1080", "4500k"), "720p": ("1280:720", "2500k"), "480p": ("854:480", "1200k")}
        dims, rate = profiles_quality[quality]
        if st.button("▶ Start Multi-Platform Live", type="primary", use_container_width=True):
            destinations = list(profiles)
            if destinations is not None:
                source_is_upload = source_mode == "Upload Video"
                if source_is_upload and uploaded is None:
                    st.error("Upload an MP4 video first.")
                elif not source_is_upload and not video_url.strip():
                    st.error("Enter a video URL first.")
                elif not destinations:
                    st.error("Enable at least one platform and enter its stream key.")
                else:
                    input_args = []
                    if source_is_upload:
                        path = STREAM_DIR / "live_input.mp4"
                        path.write_bytes(uploaded.getbuffer())
                        input_args = ["-re", "-stream_loop", "-1", "-i", str(path)]
                    else:
                        if (st.session_state.get("resolved_video_source") != video_url.strip()
                                or not st.session_state.get("resolved_video_url")):
                            st.error("Fetch the video URL first. Wait until the status says 'Ready to Live', then start streaming.")
                            input_args = None
                        else:
                            try:
                                # Signed media URLs can expire or be IP/session-bound.
                                # Resolve and verify a fresh URL immediately before FFmpeg starts.
                                media_url, headers = _resolve_video_url(video_url)
                                _probe_media_url(media_url, headers)
                                st.session_state["resolved_video_url"] = media_url
                                st.session_state["resolved_video_headers"] = headers
                                input_args = ["-re", "-rw_timeout", "20000000"]
                                if headers:
                                    header_text = _format_ffmpeg_headers(headers)
                                    input_args += ["-headers", header_text]
                                input_args += ["-i", media_url]
                            except Exception as exc:
                                st.error(
                                    "The video URL was fetched earlier, but playback verification failed "
                                    f"before streaming: {type(exc).__name__}: {exc}"
                                )
                                st.info("Click Fetch / Check Video again. If the error continues, the source may require a supported login/session.")
                                input_args = None
                    if input_args is not None:
                        _save_layers([])
                        outputs = []
                        active_names = []
                        for dest in destinations:
                            target = dest["server"].rstrip("/") + "/" + dest["key"].strip()
                            outputs.append("[f=flv:onfail=ignore]" + _tee_escape(target))
                            active_names.append(dest.get("platform", "") + " — " + dest.get("name", ""))
                        tee_target = "|".join(outputs)
                        stop_event = threading.Event()
                        try:
                            LOG_PATH.write_text("", encoding="utf-8")
                        except OSError:
                            pass
                        vf = f"scale={dims}:force_original_aspect_ratio=decrease,pad={dims}:(ow-iw)/2:(oh-ih)/2"
                        cmd = [
                            "ffmpeg", "-hide_banner", "-loglevel", "info",
                            *input_args,
                            "-thread_queue_size", "64", "-f", "rawvideo", "-pix_fmt", "rgba",
                            "-video_size", f"{CANVAS_W}x{CANVAS_H}", "-framerate", str(OVERLAY_FPS), "-i", "pipe:0",
                            "-filter_complex", f"[0:v]{vf}[base];[1:v]scale={dims}:flags=fast_bilinear[ov];[base][ov]overlay=0:0:format=auto:shortest=0[v]",
                            "-map", "[v]", "-map", "0:a?", "-t", str(int(hours * 3600)), "-r", "30",
                            "-c:v", "libx264", "-preset", "veryfast", "-b:v", rate, "-maxrate", rate, "-bufsize", rate,
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                            "-f", "tee", tee_target,
                        ]
                        try:
                            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, bufsize=0)
                            st.session_state.stream_process = process
                            st.session_state.overlay_stop_event = stop_event
                            log_reader = threading.Thread(target=_stderr_reader, args=(process,), daemon=True)
                            log_reader.start()
                            st.session_state.ffmpeg_log_thread = log_reader
                            writer = threading.Thread(target=_overlay_writer, args=(process, stop_event), daemon=True)
                            writer.start()
                            st.session_state.overlay_thread = writer
                            st.session_state.active_destinations = active_names
                            time.sleep(1.2)
                            if process.poll() is not None:
                                stop_event.set()
                                st.session_state.stream_process = None
                                st.session_state.active_destinations = []
                                try:
                                    failure_log = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                                except OSError:
                                    failure_log = "FFmpeg exited during startup."
                                st.error("FFmpeg could not start the stream. Diagnostic log:")
                                st.code(failure_log[-10000:] or "No FFmpeg diagnostic output was recorded.")
                            else:
                                st.success("FFmpeg is running. On Facebook Live Producer, wait for the incoming preview and then click Go Live.")
                                st.rerun()
                        except FileNotFoundError:
                            st.error("FFmpeg is not available on the server. Check packages.txt.")
                        except Exception as exc:
                            st.error(f"Could not start stream: {exc}")

    if running:
        _render_graphics_studio()
    if LOG_PATH.exists():
        with st.expander("FFmpeg diagnostic log", expanded=False):
            try:
                log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                st.code(log_text[-12000:] if log_text else "No FFmpeg warnings or errors have been recorded yet.")
            except OSError as exc:
                st.caption(f"Could not read log: {exc}")
    st.markdown("---")
