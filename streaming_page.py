
import os
import json
import time
import threading
import subprocess
import uuid
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
    st.caption("Yahan add ki gayi graphics running stream par overlay hoti hain. Changes live apply hoti hain; stream restart ki zaroorat nahi.")
    layers = _load_layers()

    with st.expander("🖼️ Photo / Logo add karein", expanded=False):
        photo = st.file_uploader("PNG / JPG / WEBP image", type=["png", "jpg", "jpeg", "webp"], key="overlay_photo")
        c1, c2, c3 = st.columns(3)
        px = c1.number_input("X position", 0, CANVAS_W-1, 40, key="photo_x")
        py = c2.number_input("Y position", 0, CANVAS_H-1, 40, key="photo_y")
        pw = c3.slider("Width", 40, 900, 260, key="photo_width")
        opacity = st.slider("Photo opacity", 10, 100, 100, key="photo_opacity")
        if st.button("＋ Add Photo / Logo", key="add_photo"):
            if photo is None:
                st.warning("Pehle image upload karein.")
            else:
                ext = Path(photo.name).suffix.lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                    st.error("Unsupported image format.")
                else:
                    asset_path = ASSET_DIR / f"{uuid.uuid4().hex}{ext}"
                    asset_path.write_bytes(photo.getbuffer())
                    _add_layer({"type":"photo","name":photo.name,"path":str(asset_path),"x":int(px),"y":int(py),"width":int(pw),"height":600,"opacity":int(opacity)})
                    st.success("Photo/logo live graphics mein add ho gaya.")
                    st.rerun()

    with st.expander("✍️ Text add karein", expanded=False):
        txt = st.text_input("Text", max_chars=180, key="overlay_text")
        c1, c2, c3 = st.columns(3)
        tx = c1.number_input("X", 0, CANVAS_W-1, 60, key="text_x")
        ty = c2.number_input("Y", 0, CANVAS_H-1, 60, key="text_y")
        fs = c3.slider("Font size", 14, 90, 36, key="text_size")
        color = st.color_picker("Text color", "#FFFFFF", key="text_color")
        if st.button("＋ Add Text", key="add_text"):
            if txt.strip():
                _add_layer({"type":"text","name":txt[:32],"text":txt,"x":int(tx),"y":int(ty),"font_size":int(fs),"color":color})
                st.success("Text live stream par add ho gaya.")
                st.rerun()
            else:
                st.warning("Text enter karein.")

    with st.expander("📢 Banner / Lower Third add karein", expanded=False):
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
                st.success("Banner live stream par add ho gaya.")
                st.rerun()
            else:
                st.warning("Banner text enter karein.")

    with st.expander("📜 Scrolling ticker add karein", expanded=False):
        ticker_text = st.text_input("Ticker announcement", max_chars=250, key="ticker_text")
        c1, c2, c3 = st.columns(3)
        tfs = c1.slider("Ticker font size", 16, 54, 28, key="ticker_size")
        tc = c2.color_picker("Ticker text color", "#FFFFFF", key="ticker_color")
        tb = c3.color_picker("Ticker background", "#111827", key="ticker_bg")
        speed = st.slider("Ticker speed", 40, 240, 100, key="ticker_speed")
        if st.button("＋ Add Scrolling Ticker", key="add_ticker"):
            if ticker_text.strip():
                _add_layer({"type":"ticker","name":ticker_text[:32],"text":ticker_text,"font_size":int(tfs),"color":tc,"background":tb,"speed":int(speed)})
                st.success("Scrolling ticker live ho gaya.")
                st.rerun()
            else:
                st.warning("Ticker text enter karein.")

    st.markdown("**Active graphics layers**")
    if not layers:
        st.info("Abhi koi overlay nahi. Upar se photo, text, banner ya ticker add karein.")
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
                        st.success("Changes live apply ho gayi hain.")
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
    st.caption("Overlay canvas: 1280×720, transparent background. Photo/logo ko add karte waqt position aur width set karein.")
    writer = st.session_state.get("overlay_thread")
    if writer is not None and not writer.is_alive():
        st.error("Overlay sender thread band ho gaya hai. Neeche FFmpeg log check karein.")
    st.markdown("**Graphics preview**")
    st.image(_compose_overlay(_load_layers()), caption="Transparent overlay preview (actual video ke upar composite hota hai)", use_container_width=True)


def _render_account_manager():
    st.subheader("Streaming Accounts")
    st.caption("Is live session ke liye accounts bari bari add karein. Agli visit par dobara enter karne honge.")

    profiles = _load_profiles()
    drafts_key = "stream_account_drafts"
    if drafts_key not in st.session_state:
        st.session_state[drafts_key] = []

    def account_editor(profile, is_new=False, index=0):
        pid = profile.get("id") or profile.get("_draft_id") or f"new_{index}"
        title = "New account" if is_new else profile.get("name", f"Account {index + 1}")
        with st.container(border=True):
            st.markdown(f"**{title}**")
            name = st.text_input("Account / Channel Name", value=profile.get("name", ""),
                                 placeholder="e.g. My YouTube Channel", key=f"account_name_{pid}")
            platform_options = list(PLATFORMS)
            old_platform = profile.get("platform", "YouTube")
            platform_index = platform_options.index(old_platform) if old_platform in platform_options else 0
            platform = st.selectbox("Platform", platform_options, index=platform_index,
                                    key=f"account_platform_{pid}")
            server_key = f"account_server_{pid}"
            # Set platform-specific default when the selected platform changes.
            previous_key = f"account_prev_platform_{pid}"
            previous_platform = st.session_state.get(previous_key, old_platform)
            if platform != previous_platform:
                st.session_state[server_key] = PLATFORMS.get(platform, "")
                st.session_state[previous_key] = platform
            else:
                st.session_state.setdefault(previous_key, platform)
            server = st.text_input("RTMP Server URL", value=profile.get("server") or PLATFORMS.get(platform, ""),
                                   placeholder="rtmp://...", key=server_key)
            stream_key = st.text_input("Stream Key", value=profile.get("key", ""), type="password",
                                       placeholder="Enter stream key", key=f"account_key_{pid}")
            c1, c2 = st.columns(2)
            if c1.button("Save Account", key=f"save_account_{pid}", type="primary", use_container_width=True):
                if not name.strip():
                    st.error("Account / Channel Name enter karein.")
                elif not server.strip().startswith(("rtmp://", "rtmps://")):
                    st.error("Valid RTMP Server URL enter karein.")
                elif not stream_key.strip():
                    st.error("Stream Key enter karein.")
                else:
                    updated_profile = {"id": profile.get("id") or uuid.uuid4().hex[:10],
                                       "name": name.strip(), "platform": platform,
                                       "server": server.strip(), "key": stream_key.strip()}
                    updated = [p for p in profiles if p.get("id") != updated_profile["id"]]
                    updated.append(updated_profile)
                    _save_profiles(updated)
                    st.session_state[drafts_key] = [d for d in st.session_state[drafts_key]
                                                     if d.get("_draft_id") != profile.get("_draft_id")]
                    st.success(f"{name.strip()} is live session ke liye add ho gaya.")
                    st.rerun()
            if c2.button("Delete", key=f"delete_account_{pid}", use_container_width=True):
                if not is_new and profile.get("id"):
                    _save_profiles([p for p in profiles if p.get("id") != profile.get("id")])
                st.session_state[drafts_key] = [d for d in st.session_state[drafts_key]
                                                if d.get("_draft_id") != profile.get("_draft_id")]
                st.rerun()

    if profiles:
        st.markdown("**Added accounts**")
        for index, profile in enumerate(profiles):
            account_editor(profile, is_new=False, index=index)
    else:
        account_editor({"id": None, "name": "", "platform": "YouTube",
                        "server": PLATFORMS["YouTube"], "key": ""}, is_new=True, index=0)

    for index, draft in enumerate(st.session_state[drafts_key]):
        account_editor(draft, is_new=True, index=index + len(profiles) + 1)

    c1, c2 = st.columns(2)
    if c1.button("＋ Add Other Account", key="add_other_stream_account", use_container_width=True):
        st.session_state[drafts_key].append({"_draft_id": uuid.uuid4().hex[:10], "id": None,
                                             "name": "", "platform": "YouTube",
                                             "server": PLATFORMS["YouTube"], "key": ""})
        st.rerun()
    if c2.button("Done", key="done_stream_accounts", type="primary", use_container_width=True):
        if not profiles:
            st.warning("Pehle kam az kam ek account add karein.")
        elif st.session_state[drafts_key]:
            st.warning("Pehle open account forms save ya delete karein.")
        else:
            st.session_state["stream_accounts_done"] = True
            st.success("Accounts ready. Ab live ke liye platforms select karein.")


def render_streaming_page():
    st.title("📡 Live Streaming Dashboard")
    st.caption("Ek dafa encode karke selected RTMP destinations par distribute karein.")
    st.caption("Is session mein YouTube, Facebook, TikTok ya Custom RTMP destinations add karke ek hi video ko stream karein.")
    _render_account_manager()
    st.markdown("---")
    proc = st.session_state.get("stream_process")
    running = _alive(proc)

    if running:
        st.success("Live FFmpeg process chal raha hai.")
        active = st.session_state.get("active_destinations", [])
        st.write("**Active destinations:** " + (", ".join(active) if active else "Unknown"))
        if st.button("⏹ Stop Streaming", type="primary", use_container_width=True):
            _stop_stream()
            st.session_state.active_destinations = []
            st.rerun()
    else:
        uploaded = st.file_uploader("MP4 video upload karein", type=["mp4"], key="stream_video")
        profiles = _load_profiles()
        selected_ids = st.multiselect(
            "Is live ke liye accounts select karein",
            options=[p["id"] for p in profiles],
            format_func=lambda pid: next((f"{p['platform']} — {p['name']}" for p in profiles if p["id"] == pid), pid),
            key="selected_stream_profiles",
        )
        with st.expander("One-time / manual destination (saved account ke baghair)"):
            manual_platform = st.selectbox("Platform", ["YouTube", "Facebook", "TikTok", "Custom RTMP"], key="manual_platform")
            manual_server = st.text_input("RTMP Server URL", value=PLATFORMS[manual_platform], key="manual_server")
            manual_key = st.text_input("Stream Key", type="password", key="manual_key")
            use_manual = st.checkbox("Is manual destination ko bhi include karein", key="use_manual_destination")
        hours = st.number_input("Stream duration (hours)", min_value=1, max_value=12, value=4, step=1)
        quality = st.selectbox("Output quality", ["1080p", "720p", "480p"])
        profiles_quality = {"1080p": ("1920:1080", "4500k"), "720p": ("1280:720", "2500k"), "480p": ("854:480", "1200k")}
        dims, rate = profiles_quality[quality]
        st.caption(f"{quality} • H.264 {rate} • AAC audio • Single encode")
        if st.button("▶ Start Multi-Platform Live", type="primary", use_container_width=True):
            destinations = [p for p in profiles if p["id"] in selected_ids]
            if use_manual:
                if not manual_server.strip().startswith(("rtmp://", "rtmps://")) or not manual_key.strip():
                    st.error("Manual destination ke liye valid RTMP URL aur key enter karein.")
                    destinations = None
                else:
                    destinations.append({"name": manual_platform + " (manual)", "server": manual_server.strip(), "key": manual_key.strip()})
            if destinations is not None:
                if uploaded is None:
                    st.error("Pehle MP4 video upload karein.")
                elif not destinations:
                    st.error("Kam az kam ek saved ya manual platform select karein.")
                else:
                    path = STREAM_DIR / "live_input.mp4"
                    path.write_bytes(uploaded.getbuffer())
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
                        "ffmpeg", "-hide_banner", "-loglevel", "warning",
                        "-re", "-stream_loop", "-1", "-i", str(path),
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
                        st.success("Multi-platform stream start command bhej diya gaya. Har platform par Live status verify karein.")
                        st.rerun()
                    except FileNotFoundError:
                        st.error("FFmpeg server par available nahi. packages.txt check karein.")
                    except Exception as exc:
                        st.error(f"Stream start nahi ho saki: {exc}")

    if running:
        _render_graphics_studio()
    if LOG_PATH.exists():
        with st.expander("FFmpeg diagnostic log", expanded=False):
            try:
                log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                st.code(log_text[-12000:] if log_text else "Abhi koi FFmpeg warning/error record nahi hui.")
            except OSError as exc:
                st.caption(f"Log read nahi ho saka: {exc}")
    st.markdown("---")
    st.caption("Account details sirf current app session mein rehti hain; app session khatam hone par dobara enter karni hongi. Platform ki apni live-streaming eligibility aur valid RTMP details zaroori hain.")
