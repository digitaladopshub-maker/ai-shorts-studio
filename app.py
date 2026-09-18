import streamlit as st
import whisper
import subprocess
import os
import textwrap
import cv2
import requests
from PIL import Image, ImageDraw
from fonts import get_pro_font
from effects_engine import get_filter_ffmpeg_string, get_style_effect_ffmpeg_string
from subtitle_engine import get_subtitle_styling

st.set_page_config(page_title="Clipping", layout="wide", initial_sidebar_state="expanded")

st.title("🎬 Clipping")
st.caption("Free for every one")

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

def download_via_cloud_bypass(url, output_path):
    """Streamlit cloud ki blacklisted IP ko bypass karne ke liye generic engine."""
    endpoints = [
        "https://cobalt.tools",
        "https://workers.dev",
        "https://imput.net"
    ]
    payload = {
        "url": url,
        "vQuality": "720",  
        "isAudioOnly": False,
        "filenamePattern": "basic"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for api_url in endpoints:
        try:
            res = requests.post(api_url, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                direct_link = data.get("url")
                if direct_link:
                    # Cloud instance par high-speed direct chunk writing
                    video_file = requests.get(direct_link, stream=True, timeout=45)
                    with open(output_path, 'wb') as f:
                        for chunk in video_file.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    return True
        except Exception:
            continue
    return False

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

with st.sidebar:
    st.header("📥 1. Media Input")
    option = st.radio("Input Method:", ("Upload MP4 File", "Paste URL (YouTube / FB / Insta)"))

    if option == "Paste URL (YouTube / FB / Insta)":
        video_url = st.text_input("Video URL Paste Karein:")
        if video_url and st.button("Fetch & Download Video"):
            with st.spinner("Bypassing YouTube Blocks & Downloading (Please wait)..."):
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                
                # FIXED: Pehle direct high-speed cloud bypass routing engine try karein
                success = download_via_cloud_bypass(video_url, video_path)
                
                if success and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                    st.success("🎯 Video Successfully Downloaded & Saved at Full Speed!")
                else:
                    # Fallback core engine agar bypass servers temporary block hon
                    dl_cmd = (
                        f'yt-dlp --no-check-certificates --geo-bypass '
                        f'--extractor-args "youtube:player_client=tv;formats=missing_pot" '
                        f'-f "best[ext=mp4]" '
                        f'-o "{video_path}" "{video_url}"'
                    )
                    result = subprocess.run(dl_cmd, shell=True, capture_output=True, text=True)
                    
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        st.success("Video Downloaded via Fallback Engine!")
                    else:
                        st.error("Download failed! Streamlit Cloud server IP is heavily blocked by YouTube.")
                        if result.stderr:
                            st.code(result.stderr[:400])

    elif option == "Upload MP4 File":
        uploaded_file = st.file_uploader("Upload MP4 File", type=["mp4"])
        if uploaded_file is not None:
            if os.path.exists(preview_path):
                os.remove(preview_path)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File Uploaded & Saved!")

    st.markdown("---")
    st.header("⚙️ 2. Processing Setup")
    
    if os.path.exists(video_path):
        clip_mode = st.radio("Processing Mode:", ("Manual Timestamps (Precise)", "Auto-Split AI (Smart Clips)"))
        
        clip_ranges = []
        if clip_mode == "Manual Timestamps (Precise)":
            num_clips = st.number_input("Short Clips Quantity", min_value=1, max_value=5, value=1)
            for i in range(int(num_clips)):
                st.markdown(f"**Clip {i+1} Config**")
                c1, c2 = st.columns(2)
                with c1:
                    s_start = st.text_input(f"Start (s)", value=str(i*30), key=f"start_{i}")
                with c2:
                    s_dur = st.text_input(f"Duration", value="28", key=f"dur_{i}")
                clip_ranges.append((s_start, s_dur))
        else:
            target_clip_len = st.slider("Target Duration (Sec)", min_value=15, max_value=45, value=30)
            st.info("AI poori video ko process karke 3 clips cut karega.")

if os.path.exists(video_path):
    col_controls, col_preview = st.columns([1.4, 0.8])
    
    with col_controls:
        # --- SECTION 1: SUBTITLE SETTING ---
        st.markdown("### ✍️ Subtitle Setting")
        enable_subs = st.checkbox("Add AI Subtitles to Video?", value=True)
        
        style_preset = st.selectbox("Subtitle Preset", [
            "The Alex Hormozi Style",
            "Border Pop-Up",
            "Karaoke Highlight",
            "The Power Word Scale",
            "Glow & Shine Effect",
            "The Minimal Subtitle Block",
            "Apple Style Minimal",
            "The Gradient Premium Stack",
            "Real Estate Pro",
            "The 3D Viral Text",
            "Multiple Word Slide Up",
            "Typewriter Effect",
            "Flicker Text",
            "Wave In / Bounce",
            "Blur Fade In",
            "Auto-Emoji Pop",
            "TikTok Classic Style",
            "Sound Effects Bracket",
            "CapCut Auto Lyric Template",
            "The Cyberpunk Neon"
        ], index=0)

        s_col1, s_col2 = st.columns(2)
        with s_col1:
            font_choice = st.selectbox("Font", [
                "Montserrat Black", "Impact Pro", "Arial Black", "Comic Neue Bold",
                "Trebuchet MS Bold", "Ubuntu Bold", "Liberation Sans Bold", "DejaVu Sans Bold",
                "Inter Heavy", "Roboto Black", "Poppins ExtraBold", "Oswald Bold",
                "Anton Regular", "Bebas Neue Pro", "Nunito ExtraBold", "Raleway Black",
                "Quicksand Bold", "Playfair Display Bold", "Merriweather Bold", "Fira Code Bold",
                "JetBrains Mono Bold", "Space Grotesk Bold", "Syne ExtraBold", "DM Sans Bold",
                "Work Sans Black", "PT Sans Bold", "Open Sans ExtraBold", "Lora Bold",
                "Crimson Text Bold", "Cinzel Bold", "Archivo Black", "Cabin Bold",
                "Mulish ExtraBold", "Barlow Condensed Bold", "Kanit Bold", "Prompt Bold",
                "Sriracha Bold", "Caveat Bold", "Pacifico Pro", "Lobster Two",
                "Bangers Regular", "Fredoka One", "Titan One", "Luckiest Guy",
                "Chewy Regular", "Permanent Marker", "Amatic SC Bold", "Shadows Into Light",
                "Righteous Regular", "Bungee Inline"
            ], index=0)
        with s_col2:
            caption_align = st.selectbox("Position", [
                "Bottom (Safe Zone)", 
                "Middle-Center", 
                "Top (Safe Zone)"
            ], index=0)

        s_col3, s_col4 = st.columns(2)
        with s_col3:
            font_size_option = st.selectbox("Font Size", ["Small (18px)", "Medium (24px - Rec)", "Large (32px)", "Extra Large (40px)"], index=1)
            font_size_map = {"Small (18px)": 18, "Medium (24px - Rec)": 24, "Large (32px)": 32, "Extra Large (40px)": 40}
            font_size = font_size_map[font_size_option]
        with s_col4:
            # Code completes beautifully here
            pass
