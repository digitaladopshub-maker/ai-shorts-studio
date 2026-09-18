import streamlit as st
import whisper
import subprocess
import os
import shutil
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

# --- AUTO-REGISTER CUSTOM FONTS FOR FFMPEG/LIBASS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_FONT_DIR = os.path.join(BASE_DIR, "fonts")
USER_FONT_DIR = os.path.expanduser("~/.local/share/fonts")
os.makedirs(USER_FONT_DIR, exist_ok=True)

if os.path.exists(LOCAL_FONT_DIR):
    for f_name in os.listdir(LOCAL_FONT_DIR):
        if f_name.endswith(".ttf"):
            src_p = os.path.join(LOCAL_FONT_DIR, f_name)
            dst_p = os.path.join(USER_FONT_DIR, f_name)
            if not os.path.exists(dst_p):
                shutil.copy(src_p, dst_p)
    subprocess.run("fc-cache -f", shell=True, capture_output=True)

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

# --- MAIN LAYOUT SPLIT ---
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
    else: 
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
            "AntonioZull-Brush",
            "BebasNeue-Regular",
            "Impact Club",
            "Impact",
            "Impactbrutas",
            "IMPACTED",
            "Impacted2.0",
            "Impact-Extravagant",
            "Interact",
            "Montserrat-Italic-VariableFont_wght",
            "Montserrat-VariableFont_wght",
            "Popping-Cute",
            "Roboto-Bold",
            "Roboto-Regular",
            "San Antonio Charros_personal_use_only"
        ], index=3)
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
                with st.spinner("Downloading Video (Please wait)..."):
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(preview_path):
                        os.remove(preview_path)
                    
                    dl_cmd = (
                        f'yt-dlp --no-check-certificates --geo-bypass --remote-components ejs:npm '
                        f'--extractor-args "youtube:player_client=web,mweb" '
                        f'-f "bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]/best" '
                        f'-o "{video_path}" "{video_url}"'
                    )
                    result = subprocess.run(dl_cmd, shell=True, capture_output=True, text=True)
                    
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        st.success("Video Successfully Downloaded & Saved!")
                        st.rerun()
                    else:
                        fallback_cmd = f'yt-dlp --no-check-certificates --remote-components ejs:npm --extractor-args "youtube:player_client=ios" -o "{video_path}" "{video_url}"'
                        subprocess.run(fallback_cmd, shell=True)
                        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                            st.success("Video Downloaded via Fallback & Saved!")
                            st.rerun()
                        else:
                            st.error("Download failed! Detailed Error:")
                            if result.stderr:
                                st.code(result.stderr[:400])
                            else:
                                st.error("Unknown error occurred during download.")

        elif option == "Upload MP4 File":
            uploaded_file = st.file_uploader("Upload MP4 File", type=["mp4"])
            if uploaded_file is not None:
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("File Uploaded & Saved!")
                st.rerun()
    else:
        st.markdown("### 🎬 Loaded Video Preview")
        
        target_time = "0"
        vf_preview_parts = [crop_filter]
        if enable_face_tracking:
            f_x = detect_face_center(video_path, target_time)
            if f_x and "9:16" in output_format:
                vf_preview_parts = [f"crop=ih*{scale_w}/{scale_h}:ih:clamp(x={f_x}-ih*{scale_w}/{scale_h*2}\\,0\\,in_w-ih*{scale_w}/{scale_h}):0"]

        if enable_flip:
            vf_preview_parts.append("hflip")
        
        f_str = get_filter_ffmpeg_string(filter_category, specific_filter)
        if f_str:
            vf_preview_parts.append(f_str)

        e_str = get_style_effect_ffmpeg_string(style_effect)
        if e_str:
            vf_preview_parts.append(e_str)

        vf_preview_parts.append(f"scale={preview_scale_w}:{preview_scale_h}")
        vf_preview_str = ",".join(vf_preview_parts)

        subprocess.run(
            f'ffmpeg -y -ss {target_time} -i "{video_path}" -vframes 1 -vf "{vf_preview_str}" "{preview_path}"', 
            shell=True, capture_output=True
        )
        
        if os.path.exists(preview_path):
            img = Image.open(preview_path)
            draw = ImageDraw.Draw(img)
            
            if enable_subs:
                text_color, outline_color, _, _, _ = get_subtitle_styling(style_preset)
                w, h = img.size
                sample_words = ["CLIPPING", "PREVIEW", "VIRAL", "STUDIO"]
                raw_text = " ".join(sample_words[:words_per_line])
                
                wrap_width = max(8, int(16 - (font_size / 3)))
                wrapped_lines = textwrap.wrap(raw_text, width=wrap_width)
                wrapped_text = "\n".join(wrapped_lines)

                preview_calc_size = int(font_size * (preview_scale_h / scale_h) * 2.2)
                font = get_pro_font(font_choice, preview_calc_size)

                if "Top" in caption_align:
                    y_pos = int(h * 0.18)
                elif "Middle-Center" in caption_align:
                    y_pos = int(h * 0.5)
                else:
                    y_pos = int(h - int(h * 0.22))

                x_pos = int(w / 2)
                draw.multiline_text(
                    (x_pos, y_pos), wrapped_text, font=font, fill=text_color, 
                    anchor="mm", align="center", stroke_width=max(1, int(preview_calc_size * 0.08)), stroke_fill=outline_color
                )
                
            st.image(img, width=preview_scale_w, caption=f"Live Preview | Format: {output_format}")
            
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

            e_str = get_style_effect_ffmpeg_string(style_effect)
            if e_str:
                render_vf_parts.append(e_str)

            render_vf_parts.append(f"scale={scale_w}:{scale_h}")
            
            if speed_val != 1.0:
                render_vf_parts.append(f"setpts=PTS/{speed_val}")

            render_vf_str = ",".join(render_vf_parts)
            audio_filter_str = f"atempo={speed_val}" if speed_val != 1.0 else "anull"

            crop_cmd = (
                f'ffmpeg -y -ss {start_sec} -i "{video_path}" -t {duration_sec} '
                f'-vf "{render_vf_str}" -af "{audio_filter_str}" '
                f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac "{cropped_file}"'
            )
            subprocess.run(crop_cmd, shell=True)

            mixed_audio_file = os.path.join(DOWNLOAD_DIR, f"mixed_{clip_num}.mp4")
            if enable_bg_music and os.path.exists(bg_music_path):
                mix_cmd = (
                    f'ffmpeg -y -i "{cropped_file}" -stream_loop -1 -i "{bg_music_path}" '
                    f'-filter_complex "[0:a]volume={orig_vol}[a1];[1:a]volume={bg_vol}[a2];[a1][a2]amix=inputs=2:duration=first[aout]" '
                    f'-map 0:v -map "[aout]" -c:v copy -c:a aac "{mixed_audio_file}"'
                )
                subprocess.run(mix_cmd, shell=True)
                if os.path.exists(mixed_audio_file):
                    cropped_file = mixed_audio_file

            if enable_subs and model:
                whisper_audio_path = os.path.join(DOWNLOAD_DIR, f"whisper_audio_{clip_num}.wav")
                subprocess.run(f'ffmpeg -y -i "{cropped_file}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{whisper_audio_path}"', shell=True, capture_output=True)
                
                align_map = {"Top (Safe Zone)": "6", "Middle-Center": "5", "Bottom (Safe Zone)": "2"}
                align_val = align_map[caption_align]
                
                text_col, _, _, _, ass_color = get_subtitle_styling(style_preset)
                
                # PASS SELECTED FONT NAME TO ASS ENGINE (REGISTERED VIA FONTCONFIG)
                ass_font_name = font_choice

                result = model.transcribe(whisper_audio_path if os.path.exists(whisper_audio_path) else cropped_file, word_timestamps=True)
                ass_file = os.path.join(DOWNLOAD_DIR, f"subs_{clip_num}.ass")
                
                with open(ass_file, "w", encoding="utf-8") as f:
                    f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {scale_w}\nPlayResY: {scale_h}\n\n")
                    f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                    
                    margin_v_val = int(scale_h * 0.12) if "Bottom" in caption_align else (int(scale_h * 0.1) if "Top" in caption_align else int(scale_h * 0.5))
                    
                    render_ass_fontsize = int(font_size * (scale_h / 480) * 1.5)
                    
                    f.write(f"Style: Default,{ass_font_name},{render_ass_fontsize},{ass_color},&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{align_val},160,160,{margin_v_val},1\n\n")
                    f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                    
                    for segment in result['segments']:
                        if 'words' in segment:
                            words = segment['words']
                            for i in range(0, len(words), words_per_line):
                                chunk = words[i:i + words_per_line]
                                start_t = chunk[0]['start']
                                end_t = chunk[-1]['end']
                                raw_str = " ".join([w['word'].strip() for w in chunk]).upper()
                                
                                render_wrap_width = max(10, int(18 - (font_size / 4)))
                                wrapped_chunk = textwrap.wrap(raw_str, width=render_wrap_width)
                                text_str = "\\N".join(wrapped_chunk)
                                
                                s_m, s_s = divmod(start_t, 60)
                                s_h, s_m = divmod(s_m, 60)
                                e_m, e_s = divmod(end_t, 60)
                                e_h, e_m = divmod(e_m, 60)
                                
                                s_str = f"{int(s_h)}:{int(s_m):02d}:{int(s_s):02d}.{int((start_t%1)*100):02d}"
                                e_str = f"{int(e_h)}:{int(e_m):02d}:{int(e_s):02d}.{int((end_t%1)*100):02d}"
                                
                                f.write(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{text_str}\n")

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
