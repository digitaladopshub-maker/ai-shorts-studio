import streamlit as st
import whisper
import subprocess
import os
import textwrap
import cv2
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Pro Shorts Studio", layout="wide", initial_sidebar_state="expanded")

st.title("🎬 Smart Pro AI Shorts Studio - Phase 3 (Percentage Audio)")
st.caption("Commercial-Grade AI Vertical Video, Subtitle, Face Tracking & Audio Generator")

if 'frame_time' not in st.session_state:
    st.session_state.frame_time = "0"

video_path = "input_video.mp4"
preview_path = "preview_frame.jpg"
bg_music_path = "bg_music.mp3"

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
            with st.spinner("Downloading Video..."):
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                
                dl_cmd = (
                    f'yt-dlp --no-check-certificates '
                    f'--extractor-args "youtube:player_client=ios,mweb" '
                    f'-f "b[ext=mp4]/best[ext=mp4]/best" '
                    f'-o "{video_path}" "{video_url}"'
                )
                subprocess.run(dl_cmd, shell=True)
                if os.path.exists(video_path):
                    st.success("Video Ready!")
                else:
                    st.error("Download failed. Use File Upload option.")

    elif option == "Upload MP4 File":
        uploaded_file = st.file_uploader("Upload MP4 File", type=["mp4"])
        if uploaded_file is not None:
            if os.path.exists(preview_path):
                os.remove(preview_path)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File Uploaded!")

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
    tab_subs, tab_audio = st.tabs(["✍️ Subtitle Customizer & Live Studio", "🎵 Audio & Background Music"])
    
    with tab_subs:
        enable_subs = st.checkbox("Add AI Subtitles to Video?", value=True)
        enable_face_tracking = st.checkbox("🤖 Enable Smart AI Face Tracking (Center Crop on Speaker)", value=True)
        
        if enable_subs:
            col_controls, col_preview = st.columns([1.2, 0.8])
            
            with col_controls:
                st.subheader("🎨 Captions Styling Controls")
                col_a, col_b = st.columns(2)
                with col_a:
                    caption_style = st.selectbox("Text Color Style", [
                        "Yellow Bold (Alex Hormozi)", "White + Black Outline", 
                        "Neon Green + Shadow", "Red Alert Style"
                    ], index=0)
                with col_b:
                    anim_effect = st.selectbox("Animation Transition", [
                        "Pop-In Scale (Fast Zoom)", "Fade In / Fade Out", "Standard Pop-Up"
                    ], index=0)

                st.markdown("---")
                st.subheader("📐 Typography & Position")
                caption_align = st.selectbox("Position Alignment", ["Bottom (Recommended)", "Middle-Center", "Top"], index=0)
                words_per_line = st.slider("Words Per Line Box", min_value=1, max_value=5, value=2)
                font_size = st.slider("Font Size Customizer", min_value=12, max_value=40, value=22)
                vert_margin = st.slider("Vertical Bottom Offset (Height)", min_value=30, max_value=300, value=180)

            with col_preview:
                st.subheader("🖼 Instant Live Preview")
                prev_sec = clip_ranges[0][0] if (clip_mode == "Manual Timestamps (Precise)" and clip_ranges) else "0"
                
                if st.button("🔄 Refresh Preview Frame", use_container_width=True):
                    st.session_state.frame_time = prev_sec
                    if os.path.exists(preview_path):
                        os.remove(preview_path)

                target_time = st.session_state.frame_time if st.session_state.frame_time else prev_sec
                
                vf_crop = "crop=ih*9/16:ih,scale=540:960"
                if enable_face_tracking:
                    f_x = detect_face_center(video_path, target_time)
                    if f_x:
                        vf_crop = f"crop=ih*9/16:ih:clamp(x={f_x}-ih*9/32\\,0\\,in_w-ih*9/16):0,scale=540:960"

                subprocess.run(
                    f'ffmpeg -y -ss {target_time} -i "{video_path}" -vframes 1 -vf "{vf_crop}" "{preview_path}"', 
                    shell=True, capture_output=True
                )
                
                if os.path.exists(preview_path):
                    img = Image.open(preview_path)
                    draw = ImageDraw.Draw(img)
                    colors = {
                        "Yellow Bold (Alex Hormozi)": ("#FFFF00", "#000000"),
                        "White + Black Outline": ("#FFFFFF", "#000000"),
                        "Neon Green + Shadow": ("#00FF00", "#000000"),
                        "Red Alert Style": ("#FF0000", "#FFFFFF")
                    }
                    text_color, outline_color = colors[caption_style]
                    w, h = img.size
                    sample_words = ["SAMPLE", "CAPTION", "TEXT", "PREVIEW", "STYLE"]
                    raw_text = " ".join(sample_words[:words_per_line])
                    
                    if anim_effect == "Pop-In Scale (Fast Zoom)":
                        raw_text = "💥 " + raw_text
                    elif anim_effect == "Fade In / Fade Out":
                        raw_text = "✨ " + raw_text

                    wrapped_lines = textwrap.wrap(raw_text, width=14)
                    wrapped_text = "\n".join(wrapped_lines)

                    font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
                    if not os.path.exists(font_path):
                        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                    
                    try:
                        font = ImageFont.truetype(font_path, int(font_size * 1.6))
                    except:
                        font = ImageFont.load_default()

                    if caption_align == "Top":
                        y_pos = int(h * 0.12)
                    elif caption_align == "Middle-Center":
                        y_pos = int(h * 0.5)
                    else:
                        y_pos = int(h - (vert_margin * 1.8))

                    x_pos = int(w / 2)
                    draw.multiline_text(
                        (x_pos, y_pos), wrapped_text, font=font, fill=text_color, 
                        anchor="mm", align="center", stroke_width=3, stroke_fill=outline_color
                    )
                    st.image(img, caption=f"Live Subtitle Preview (Frame at {target_time}s)", use_container_width=True)

    with tab_audio:
        st.subheader("🎵 Background Music & Audio Mixing (Percentage System)")
        enable_bg_music = st.checkbox("Add Background Music Track?", value=False)
        bg_music_file = None
        if enable_bg_music:
            uploaded_music = st.file_uploader("Upload Background MP3 Audio File", type=["mp3", "wav"])
            if uploaded_music is not None:
                with open(bg_music_path, "wb") as f:
                    f.write(uploaded_music.getbuffer())
                st.success("Background Music Loaded!")
                bg_music_file = bg_music_path

            col_vol1, col_vol2 = st.columns(2)
            with col_vol1:
                # Percentage Sliders: 0% to 200% for voice, 0% to 100% for background music
                orig_vol_pct = st.slider("Original Voice Volume (%)", min_value=0, max_value=200, value=100, step=5)
                orig_vol = orig_vol_pct / 100.0
            with col_vol2:
                bg_vol_pct = st.slider("Background Music Volume (%)", min_value=0, max_value=100, value=15, step=1)
                bg_vol = bg_vol_pct / 100.0

    st.markdown("---")
    if st.button("🚀 Render Shorts Batch Now", type="primary", use_container_width=True):
        tasks = []
        if clip_mode == "Manual Timestamps (Precise)":
            for idx, (s_st, s_du) in enumerate(clip_ranges):
                try:
                    t_start, t_dur = int(s_st), int(s_du)
                except:
                    t_start, t_dur = idx * 30, 28
                tasks.append((idx + 1, t_start, t_dur))
        else:
            tasks = [(1, 0, target_clip_len), (2, target_clip_len + 5, target_clip_len), (3, (target_clip_len*2)+10, target_clip_len)]

        model = whisper.load_model("base") if enable_subs else None
        generated_clips = []

        with st.spinner("Processing High-Quality Shorts with AI Engine & Audio Percentages..."):
            for clip_num, start_sec, duration_sec in tasks:
                cropped_file = f"cropped_{clip_num}.mp4"
                final_file = f"final_short_{clip_num}.mp4"
                
                vf_crop_hd = "crop=ih*9/16:ih,scale=1080:1920"
                if enable_face_tracking:
                    f_x = detect_face_center(video_path, start_sec)
                    if f_x:
                        vf_crop_hd = f"crop=ih*9/16:ih:clamp(x={f_x}-ih*9/32\\,0\\,in_w-ih*9/16):0,scale=1080:1920"

                crop_cmd = (
                    f'ffmpeg -y -ss {start_sec} -i "{video_path}" -t {duration_sec} '
                    f'-vf "{vf_crop_hd}" '
                    f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac "{cropped_file}"'
                )
                subprocess.run(crop_cmd, shell=True)

                mixed_audio_file = f"mixed_{clip_num}.mp4"
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
                    align_map = {"Top": "6", "Middle-Center": "5", "Bottom (Recommended)": "2"}
                    align_val = align_map[caption_align]

                    result = model.transcribe(cropped_file, word_timestamps=True)
                    ass_file = f"subs_{clip_num}.ass"
                    
                    with open(ass_file, "w", encoding="utf-8") as f:
                        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
                        f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                        f.write(f"Style: Default,Arial,{font_size*2.2},&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{align_val},108,108,{vert_margin},1\n\n")
                        f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                        
                        for segment in result['segments']:
                            if 'words' in segment:
                                words = segment['words']
                                for i in range(0, len(words), words_per_line):
                                    chunk = words[i:i + words_per_line]
                                    start_t = chunk[0]['start']
                                    end_t = chunk[-1]['end']
                                    raw_str = " ".join([w['word'].strip() for w in chunk]).upper()
                                    
                                    wrapped_chunk = textwrap.wrap(raw_str, width=15)
                                    text_str = "\\N".join(wrapped_chunk)
                                    
                                    s_m, s_s = divmod(start_t, 60)
                                    s_h, s_m = divmod(s_m, 60)
                                    e_m, e_s = divmod(end_t, 60)
                                    e_h, e_m = divmod(e_m, 60)
                                    
                                    s_str = f"{int(s_h)}:{int(s_m):02d}:{int(s_s):02d}.{int((start_t%1)*100):02d}"
                                    e_str = f"{int(e_h)}:{int(e_m):02d}:{int(e_s):02d}.{int((end_t%1)*100):02d}"
                                    
                                    if anim_effect == "Pop-In Scale (Fast Zoom)":
                                        anim_tag = r"{\t(0,80,\fscx115\fscy115)\t(80,160,\fscx100\fscy100)}"
                                    elif anim_effect == "Fade In / Fade Out":
                                        anim_tag = r"{\fad(100,100)}"
                                    else:
                                        anim_tag = ""
                                        
                                    f.write(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{anim_tag}{text_str}\n")

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
else:
    st.info("👈 Media Input Sidebar se video upload karein ya URL paste karein to start.")
