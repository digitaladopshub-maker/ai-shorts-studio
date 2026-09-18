import streamlit as st
import whisper
import subprocess
import os
import textwrap
import cv2
from PIL import Image, ImageDraw
from fonts import get_pro_font
from effects_engine import get_filter_ffmpeg_string, get_style_effect_ffmpeg_string
from subtitle_engine import get_subtitle_styling

st.set_page_config(page_title="AI Clipping Studio", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .main-title { font-size: 26px; font-weight: 700; color: #111827; margin-bottom: 0px; }
        .sub-text { font-size: 13px; color: #6b7280; margin-bottom: 15px; }
        div.stButton > button:first-child { border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

if 'frame_time' not in st.session_state:
    st.session_state.frame_time = "0"

if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = 0

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

video_path = os.path.join(DOWNLOAD_DIR, "input_video.mp4")
preview_path = os.path.join(DOWNLOAD_DIR, "preview_frame.jpg")
bg_music_path = os.path.join(DOWNLOAD_DIR, "bg_music.mp3")

def detect_face_center(v_path, start_sec):
    try:
        cap = cv2.VideoCapture(v_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, int(start_sec) * 1000)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            return None
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            return None
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            x, y, w, h = faces[0]
            return x + (w // 2)
    except Exception:
        return None
    return None

# --- HEADER SECTION ---
st.markdown('<p class="main-title">AI Clipping</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Transform your long video into multiple highlight reels—in just one click!</p>', unsafe_allow_html=True)

# --- MAIN LAYOUT SPLIT (Left: Preview / Input, Right: Controls & Formats) ---
col_left, col_right = st.columns([1.0, 1.3], gap="large")

with col_right:
    # --- 1. OUTPUT FORMAT SECTION ---
    fmt_col1, fmt_col2 = st.columns([1.2, 2.8])
    with fmt_col1:
        st.markdown("<h4 style='padding-top: 5px;'>Output Format</h4>", unsafe_allow_html=True)
    with fmt_col2:
        output_format = st.radio(
            "Output Format Options", 
            ["9:16 Vertical", "16:9 Landscape", "1:1 Square"], 
            horizontal=True, 
            label_visibility="collapsed"
        )

    if "9:16" in output_format:
        scale_w, scale_h = 1080, 1920
        crop_filter = "crop=ih*9/16:ih"
        preview_scale_w, preview_scale_h = 270, 480
    elif "16:9" in output_format:
        scale_w, scale_h = 1920, 1080
        crop_filter = "crop=iw:iw*9/16"
        preview_scale_w, preview_scale_h = 480, 270
    else: # 1:1 Square
        scale_w, scale_h = 1080, 1080
        crop_filter = "crop=min(iw\\,ih):min(iw\\,ih)"
        preview_scale_w, preview_scale_h = 350, 350

    st.markdown("---")

    # --- 2. SUBTITLE / CAPTION SETTING ---
    st.markdown("### ✍️ Subtitle Setting")
    enable_subs = st.checkbox("Add AI Subtitles to Video?", value=True)
    
    style_preset = st.selectbox("Subtitle Preset", [
        "The Alex Hormozi Style", "Border Pop-Up", "Karaoke Highlight", "The Power Word Scale", 
        "Glow & Shine Effect", "The Minimal Subtitle Block", "Apple Style Minimal", "The Gradient Premium Stack", 
        "Real Estate Pro", "The 3D Viral Text", "Multiple Word Slide Up", "Typewriter Effect", 
        "Flicker Text", "Wave In / Bounce", "Blur Fade In", "Auto-Emoji Pop", 
        "TikTok Classic Style", "Sound Effects Bracket", "CapCut Auto Lyric Template", "The Cyberpunk Neon"
    ], index=0)

    s_col1, s_col2 = st.columns(2)
    with s_col1:
        font_choice = st.selectbox("Font", [
            "Montserrat Black", "Impact Pro", "Arial Black", "Comic Neue Bold", "Ubuntu Bold", "Inter Heavy", "Roboto Black"
        ], index=0)
    with s_col2:
        caption_align = st.selectbox("Position", ["Bottom (Safe Zone)", "Middle-Center", "Top (Safe Zone)"], index=0)

    s_col3, s_col4 = st.columns(2)
    with s_col3:
        font_size_option = st.selectbox("Font Size", ["Small (18px)", "Medium (24px - Rec)", "Large (32px)", "Extra Large (40px)"], index=1)
        font_size_map = {"Small (18px)": 18, "Medium (24px - Rec)": 24, "Large (32px)": 32, "Extra Large (40px)": 40}
        font_size = font_size_map[font_size_option]
    with s_col4:
        words_per_line_option = st.selectbox("Words Per Line", ["1 Word", "2 Words (Recommended)", "3 Words", "4 Words", "5 Words"], index=1)
        wpl_map = {"1 Word": 1, "2 Words (Recommended)": 2, "3 Words": 3, "4 Words": 4, "5 Words": 5}
        words_per_line = wpl_map[words_per_line_option]

    st.markdown("---")

    # --- 3. PROCESSING MODE SELECTION ---
    st.markdown("### ⚙️ Processing Mode Selection")
    clip_mode = st.radio("Processing Mode Selection:", ("Manual Timestamps (Precise)", "Auto-Split AI (Smart Clips)"), label_visibility="collapsed")
    
    clip_ranges = []
    if clip_mode == "Manual Timestamps (Precise)":
        num_clips = st.number_input("Short Clips Quantity", min_value=1, max_value=5, value=1)
        for i in range(int(num_clips)):
            c1, c2 = st.columns(2)
            with c1:
                s_start = st.text_input(f"Clip {i+1} Start (s)", value=str(i*30), key=f"start_{i}")
            with c2:
                s_dur = st.text_input(f"Clip {i+1} Duration", value="28", key=f"dur_{i}")
            clip_ranges.append((s_start, s_dur))
    else:
        target_clip_len = st.slider("Target Duration (Sec)", min_value=15, max_value=45, value=30)
        st.info("AI will automatically split video into smart clips.")

    st.markdown("---")

    # --- 4. VIDEO & AUDIO SETTINGS ---
    with st.expander("🎥 Video Filters & 🎵 Audio Settings"):
        filter_category = st.selectbox("Filter Category", [
            "High Quality & Aesthetic Filters (For Face & Body)",
            "🎬 Cinematic & Vibe Filters (For Travel & Vlogs)",
            "🤖 Viral AI & Special Effects Filters"
        ], index=0, key=f"fc_{st.session_state.reset_trigger}")

        if filter_category == "High Quality & Aesthetic Filters (For Face & Body)":
            specific_filter_options = ["None", "iPhone HD", "HD Glamour Filter", "Flash CCD", "Universal Sunset", "Bold Glamour", "Bubblegum"]
        elif filter_category == "🎬 Cinematic & Vibe Filters (For Travel & Vlogs)":
            specific_filter_options = ["None", "Cinematic Glow / HD", "Green Lake", "Renoir / Reno", "Moon Rise", "Bad Bunny", "Cool Vibes"]
        else:
            specific_filter_options = ["None", "Cartoon Filter AI", "Barbie Girl AI / Princess", "Kid Teen Now Aged", "Falling Filter", "2016 Filter", "Velocity x Color AD", "Thermal Effect", "Dreamy Halo"]

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            specific_filter = st.selectbox("Select Filter", specific_filter_options, index=0, key=f"sf_{st.session_state.reset_trigger}")
        with f_col2:
            style_effect = st.selectbox("Style and Effects", ["None", "AI Autofill", "Velocity (Auto Velocity)", "3D Zoom Pro", "Camera Shake", "VHS Glitch Overlay"], index=0, key=f"se_{st.session_state.reset_trigger}")

        v_col1, v_col2 = st.columns(2)
        with v_col1:
            enable_flip = st.checkbox("🔄 Horizontal Flip", value=False, key=f"flp_{st.session_state.reset_trigger}")
        with v_col2:
            video_speed = st.selectbox("Video Speed", ["1.0x (Normal)", "1.1x (Fast Viral)", "1.25x (Super Fast)"], index=0, key=f"spd_{st.session_state.reset_trigger}")
            speed_val = 1.0 if "1.0x" in video_speed else (1.1 if "1.1x" in video_speed else 1.25)

        if st.button("🔄 Reset Video Filters & Effects"):
            st.session_state.reset_trigger += 1
            st.rerun()

        enable_bg_music = st.checkbox("Add Background Music Track?", value=False)
        bg_music_file = None
        if enable_bg_music:
            uploaded_music = st.file_uploader("Upload Background MP3 Audio File", type=["mp3", "wav"])
            if uploaded_music is not None:
                with open(bg_music_path, "wb") as f:
                    f.write(uploaded_music.getbuffer())
                st.success("Background Music Loaded!")
                bg_music_file = bg_music_path

            ac1, ac2 = st.columns(2)
            with ac1:
                orig_vol_pct = st.slider("Original Voice Volume (%)", min_value=0, max_value=200, value=100, step=5)
                orig_vol = orig_vol_pct / 100.0
            with ac2:
                bg_vol_pct = st.slider("Background Music Volume (%)", min_value=0, max_value=100, value=15, step=1)
                bg_vol = bg_vol_pct / 100.0

        enable_face_tracking = st.checkbox("Enable Smart AI Face Tracking", value=True)

    render_clicked = st.button("🚀 Render Shorts Batch Now", type="primary", use_container_width=True)

with col_left:
    if not os.path.exists(video_path):
        st.markdown("### 📥 Media Input")
        option = st.radio("Input Method:", ("Upload MP4 File", "Paste URL (YouTube / FB / Insta)"))

        if option == "Paste URL (YouTube / FB / Insta)":
            video_url = st.text_input("Video URL Paste Karein:")
            if video_url and st.button("Fetch & Download Video"):
                with st.spinner("Downloading Video via Bypass Client (Please wait)..."):
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(preview_path):
