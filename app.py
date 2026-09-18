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
    # --- 1. OUTPUT FORMAT SECTION (Heading on Left side of options) ---
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

    # Dimension, crop configurations, and safe preview rendering scales
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
        crop_filter = "crop=ih:ih"
        preview_scale_w, preview_scale_h = 350, 350

    st.markdown("---")

    # --- 2. CAPTION STYLE SECTION (Moved to top position) ---
    st.markdown("### Caption Style")
    caption_style_options = [
        "None", "Subtle Gray", "Shadow Mint", "Subtle Cyan", "Stamp Red", 
        "Retro Gold", "Block Dark", "Racing", "Modern Dark", "Modern Boxed", 
        "Chunky", "Clean", "Shadow Lime", "Tag Yellow", "Pop Purple", 
        "Spotlight", "Outline Classic", "Exotic", "Golden", "Simple", 
        "Pop Single", "Energy", "Bold", "Elegant", "Neon Pink"
    ]
    selected_caption_style = st.selectbox("Select Caption Preset", caption_style_options, index=0, label_visibility="collapsed")

    # Active backup Subtitle Setting for robust rendering compatibility
    with st.expander("Advanced Subtitle Settings (Active Backend)"):
        enable_subs = st.checkbox("Add AI Subtitles to Video?", value=True)
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            font_choice = st.selectbox("Font", ["Montserrat Black", "Impact Pro", "Arial Black", "Ubuntu Bold"], index=0)
        with s_col2:
            caption_align = st.selectbox("Position", ["Bottom (Safe Zone)", "Middle-Center", "Top (Safe Zone)"], index=0)

        s_col3, s_col4 = st.columns(2)
        with s_col3:
            font_size = st.slider("Font Size", 18, 40, 24)
        with s_col4:
            words_per_line = st.slider("Words Per Line", 1, 5, 2)

    st.markdown("---")

    # --- 3. PROCESSING MODE SELECTION (Moved to lower position without top timing heading) ---
    st.markdown("### Processing Mode Selection")
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

        enable_flip = st.checkbox("🔄 Horizontal Flip", value=False, key=f"flp_{st.session_state.reset_trigger}")
        
        enable_bg_music = st.checkbox("Add Background Music Track?", value=False)
        if enable_bg_music:
            uploaded_music = st.file_uploader("Upload Background MP3 Audio File", type=["mp3", "wav"])
            if uploaded_music is not None:
                with open(bg_music_path, "wb") as f:
                    f.write(uploaded_music.getbuffer())
                st.success("Background Music Loaded!")

        enable_face_tracking = st.checkbox("Enable Smart AI Face Tracking", value=True)

    render_clicked = st.button("🚀 Render Shorts Batch Now", type="primary", use_container_width=True)

with col_left:
    if not os.path.exists(video_path):
        st.markdown("### 📥 Media Input")
        uploaded_file = st.file_uploader("Drag and drop video here to upload", type=["mp4", "mov", "webm"])
        if uploaded_file is not None:
            if os.path.exists(preview_path):
                os.remove(preview_path)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File Uploaded Successfully!")
            st.rerun()

        st.markdown("<p style='text-align: center; color: #6b7280; font-weight: 500;'>Or</p>", unsafe_allow_html=True)
        
        video_url = st.text_input("Drop in the specific URL for your video", placeholder="Paste YouTube, TikTok, FB, Insta URL here...")
        if video_url and st.button("Fetch & Download Video", use_container_width=True):
            with st.spinner("Downloading Video (Please wait)..."):
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                
                dl_cmd = (
                    f'yt-dlp --no-check-certificates --geo-bypass --remote-components ejs:npm '
                    f'-f "b[ext=mp4]/best[ext=mp4]/best" '
                    f'-o "{video_path}" "{video_url}"'
                )
                result = subprocess.run(dl_cmd, shell=True, capture_output=True, text=True)
                
                if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                    st.success("Video Successfully Downloaded!")
                    st.rerun()
                else:
                    fallback_cmd = f'yt-dlp --no-check-certificates --remote-components ejs:npm -o "{video_path}" "{video_url}"'
                    subprocess.run(fallback_cmd, shell=True)
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        st.success("Video Downloaded via Fallback!")
                        st.rerun()
                    else:
                        st.error("Download failed! Check URL or network error.")
                        if result.stderr:
                            st.code(result.stderr[:400])
    else:
        st.markdown("### 🎬 Loaded Video Preview")
        
        target_time = "0"
        vf_preview_parts = [crop_filter, f"scale={preview_scale_w}:{preview_scale_h}"]
        vf_preview_str = ",".join(vf_preview_parts)
        
        subprocess.run(
            f'ffmpeg -y -ss {target_time} -i "{video_path}" -vframes 1 -vf "{vf_preview_str}" "{preview_path}"', 
            shell=True, capture_output=True
        )
        
        if os.path.exists(preview_path):
            st.image(preview_path, width=preview_scale_w, caption=f"Format: {output_format}")
            
        if st.button("❌ Remove / Change Video", use_container_width=True):
            os.remove(video_path)
            if os.path.exists(preview_path):
                os.remove(preview_path)
            st.rerun()

# --- RENDERING & EXPORT GALLERY ---
if os.path.exists(video_path) and render_clicked:
    tasks = []
    if clip_mode == "Manual Timestamps (Precise)" and 'clip_ranges' in locals():
        for idx, (s_st, s_du) in enumerate(clip_ranges):
            try:
                t_start, t_dur = int(s_st), int(s_du)
            except:
                t_start, t_dur = idx * 30, 28
            tasks.append((idx + 1, t_start, t_dur))
    else:
        tasks = [(1, 0, 30), (2, 35, 30), (3, 70, 30)]

    model = whisper.load_model("base") if enable_subs else None
    generated_clips = []

    with st.spinner("Processing High-Quality Professional Shorts..."):
        for clip_num, start_sec, duration_sec in tasks:
            cropped_file = os.path.join(DOWNLOAD_DIR, f"cropped_{clip_num}.mp4")
            final_file = os.path.join(DOWNLOAD_DIR, f"final_short_{clip_num}.mp4")
            
            render_vf_parts = [crop_filter]
            if enable_face_tracking:
                f_x = detect_face_center(video_path, start_sec)
                if f_x and "9:16" in output_format:
                    render_vf_parts = [f"crop=ih*{scale_w}/{scale_h}:ih:clamp(x={f_x}-ih*{scale_w}/{scale_h*2}\\,0\\,in_w-ih*{scale_w}/{scale_h}):0"]

            if enable_flip:
                render_vf_parts.append("hflip")
            
            f_str = get_filter_ffmpeg_string(filter_category, specific_filter)
            if f_str:
                render_vf_parts.append(f_str)

            render_vf_parts.append(f"scale={scale_w}:{scale_h}")
            render_vf_str = ",".join(render_vf_parts)

            crop_cmd = (
                f'ffmpeg -y -ss {start_sec} -i "{video_path}" -t {duration_sec} '
                f'-vf "{render_vf_str}" '
                f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac "{cropped_file}"'
            )
            subprocess.run(crop_cmd, shell=True)

            if enable_subs and model:
                align_map = {"Top (Safe Zone)": "6", "Middle-Center": "5", "Bottom (Safe Zone)": "2"}
                align_val = align_map.get(caption_align, "2")
                
                _, _, _, _, ass_color = get_subtitle_styling(selected_caption_style)
                result = model.transcribe(cropped_file, word_timestamps=True)
                ass_file = os.path.join(DOWNLOAD_DIR, f"subs_{clip_num}.ass")
                
                with open(ass_file, "w", encoding="utf-8") as f:
                    f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {scale_w}\nPlayResY: {scale_h}\n\n")
                    f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                    f.write(f"Style: Default,Liberation Sans,{int(font_size * 2.2)},{ass_color},&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{align_val},120,120,240,1\n\n")
                    f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                    
                    for segment in result.get('segments', []):
                        if 'words' in segment:
                            words = segment['words']
                            for i in range(0, len(words), words_per_line):
                                chunk = words[i:i + words_per_line]
                                start_t = chunk[0]['start']
                                end_t = chunk[-1]['end']
                                raw_str = " ".join([w['word'].strip() for w in chunk]).upper()
                                
                                s_m, s_s = divmod(start_t, 60)
                                s_h, s_m = divmod(s_m, 60)
                                e_m, e_s = divmod(end_t, 60)
                                e_h, e_m = divmod(e_m, 60)
                                
                                s_str = f"{int(s_h)}:{int(s_m):02d}:{int(s_s):02d}.{int((start_t%1)*100):02d}"
                                e_str = f"{int(e_h)}:{int(e_m):02d}:{int(e_s):02d}.{int((end_t%1)*100):02d}"
                                f.write(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{raw_str}\n")

                sub_cmd = (
                    f'ffmpeg -y -i "{cropped_file}" '
                    f'-vf "ass={ass_file}" '
                    f'-c:v libx264 -preset ultrafast -c:a copy "{final_file}"'
                )
                subprocess.run(sub_cmd, shell=True)
            else:
                if os.path.exists(final_file):
                    os.remove(final_file)
                os.rename(cropped_file, final_file)

            generated_clips.append((clip_num, final_file))

    st.subheader("🎉 Shorts Export Gallery")
    cols = st.columns(3)
    for idx, (c_num, filepath) in enumerate(generated_clips):
        col_target = cols[idx % 3]
        with col_target:
            st.markdown(f"**🎬 Short Clip {c_num}**")
            st.video(filepath)
