import streamlit as st
import whisper
import subprocess
import os
import textwrap
import cv2
from PIL import Image, ImageDraw
from fonts import get_pro_font

st.set_page_config(page_title="Clipping", layout="wide", initial_sidebar_state="expanded")

st.title("🎬 Clipping")
st.caption("Free for every one")

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
    tab_subs, tab_audio = st.tabs(["✍️ Ultimate Subtitle Studio", "🎵 Audio & Background Music"])
    
    with tab_subs:
        enable_subs = st.checkbox("Add AI Subtitles to Video?", value=True)
        
        if enable_subs:
            col_controls, col_preview = st.columns([1.5, 0.7])
            
            with col_controls:
                r1_col1, r1_col2 = st.columns(2)
                with r1_col1:
                    style_preset = st.selectbox("Preset", [
                        "1. ⚡ Alex Hormozi (Yellow Bold + Pop)",
                        "2. 💎 Cyberpunk Neon (Green + Glow)",
                        "3. 🌊 Ocean Breeze (Cyan + Shadow)",
                        "4. 🔥 Sunset Blaze (Orange Gradient)",
                        "5. 👑 Royal Gold (Metallic Gold)",
                        "6. 🚀 TikTok Viral (Electric Blue)",
                        "7. 🩸 Matrix Code (Lime Green)",
                        "8. 🎯 Minimalist Clean (White)",
                        "9. 🚨 Emergency Alert (Blood Red)",
                        "10. 💜 Purple Haze (Neon Purple)",
                        "11. 🍋 Lemon Punch (Vibrant Yellow)",
                        "12. ⚡ Flash White (Thick Border)",
                        "13. 🍊 Tangerine Dream (Neon Orange)",
                        "14. 🧊 Ice Glacier (Ice Blue)",
                        "15. 🥑 Avocado Pop (Neon Lime)",
                        "16. 🔮 Mystic Violet (Magenta)",
                        "17. 🍫 Caramel Gold (Warm Amber)",
                        "18. 🧨 Firecracker (Bright Coral)",
                        "19. 🌿 Emerald Fresh (Mint Green)",
                        "20. 🦄 Cyber Unicorn (Dual Tone)"
                    ], index=0)

                with r1_col2:
                    font_choice = st.selectbox("Font", [
                        "1. Montserrat Black", "2. Impact Pro", "3. Arial Black", "4. Comic Neue Bold",
                        "5. Trebuchet MS Bold", "6. Ubuntu Bold", "7. Liberation Sans Bold", "8. DejaVu Sans Bold",
                        "9. Inter Heavy", "10. Roboto Black", "11. Poppins ExtraBold", "12. Oswald Bold",
                        "13. Anton Regular", "14. Bebas Neue Pro", "15. Nunito ExtraBold", "16. Raleway Black",
                        "17. Quicksand Bold", "18. Playfair Display Bold", "19. Merriweather Bold", "20. Fira Code Bold",
                        "21. JetBrains Mono Bold", "22. Space Grotesk Bold", "23. Syne ExtraBold", "24. DM Sans Bold",
                        "25. Work Sans Black", "26. PT Sans Bold", "27. Open Sans ExtraBold", "28. Lora Bold",
                        "29. Crimson Text Bold", "30. Cinzel Bold", "31. Archivo Black", "32. Cabin Bold",
                        "33. Mulish ExtraBold", "34. Barlow Condensed Bold", "35. Kanit Bold", "36. Prompt Bold",
                        "37. Sriracha Bold", "38. Caveat Bold", "39. Pacifico Pro", "40. Lobster Two",
                        "41. Bangers Regular", "42. Fredoka One", "43. Titan One", "44. Luckiest Guy",
                        "45. Chewy Regular", "46. Permanent Marker", "47. Amatic SC Bold", "48. Shadows Into Light",
                        "49. Righteous Regular", "50. Bungee Inline"
                    ], index=0)

                r2_col1, r2_col2 = st.columns(2)
                with r2_col1:
                    caption_align = st.selectbox("Position", [
                        "Bottom (Safe Zone)", 
                        "Middle-Center", 
                        "Top (Safe Zone)"
                    ], index=0)

                with r2_col2:
                    font_size_option = st.selectbox("Font Size", ["Small (18px)", "Medium (24px - Rec)", "Large (32px)", "Extra Large (40px)"], index=1)
                    font_size_map = {"Small (18px)": 18, "Medium (24px - Rec)": 24, "Large (32px)": 32, "Extra Large (40px)": 40}
                    font_size = font_size_map[font_size_option]

                r3_col1, r3_col2 = st.columns(2)
                with r3_col1:
                    words_per_line_option = st.selectbox("Words Per Line", ["1 Word", "2 Words (Recommended)", "3 Words", "4 Words", "5 Words"], index=1)
                    wpl_map = {"1 Word": 1, "2 Words (Recommended)": 2, "3 Words": 3, "4 Words": 4, "5 Words": 5}
                    words_per_line = wpl_map[words_per_line_option]
                with r3_col2:
                    video_speed = st.selectbox("Video Speed (Retention)", ["1.0x (Normal)", "1.1x (Fast Viral)", "1.25x (Super Fast)"], index=0)
                    speed_val = 1.0 if "1.0x" in video_speed else (1.1 if "1.1x" in video_speed else 1.25)

                # Reordered: Style and Effects moved up, Horizontal Flip moved down
                r4_col1, r4_col2 = st.columns(2)
                with r4_col1:
                    clipchamp_effect = st.selectbox("✨ Style and Effects", ["None", "Soft Vignette Glow", "VHS Glitch Overlay", "Cinematic Letterbox (Cinemascope)", "Bokeh Blur Background Touch"], index=0)
                with r4_col2:
                    color_filter = st.selectbox("Cinematic Filter", ["Normal", "Cyberpunk Glow", "High Contrast", "Warm Cinematic", "Vintage Film 70s", "HDR Vibrant"], index=0)

                enable_flip = st.checkbox("🔄 Horizontal Flip (Anti-Copyright)", value=False)
                enable_face_tracking = st.checkbox("Enable Smart AI Face Tracking", value=True)

                st.markdown("---")
                render_clicked = st.button("🚀 Render Shorts Batch Now", type="primary", use_container_width=True)

            with col_preview:
                target_time = clip_ranges[0][0] if (clip_mode == "Manual Timestamps (Precise)" and clip_ranges) else "0"
                
                vf_parts = []
                if enable_face_tracking:
                    f_x = detect_face_center(video_path, target_time)
                    if f_x:
                        vf_parts.append(f"crop=ih*9/16:ih:clamp(x={f_x}-ih*9/32\\,0\\,in_w-ih*9/16):0")
                    else:
                        vf_parts.append("crop=ih*9/16:ih")
                else:
                    vf_parts.append("crop=ih*9/16:ih")

                if enable_flip:
                    vf_parts.append("hflip")
                
                if color_filter == "Cyberpunk Glow":
                    vf_parts.append("eq=saturation=1.4:contrast=1.2")
                elif color_filter == "High Contrast":
                    vf_parts.append("eq=contrast=1.3:brightness=0.05")
                elif color_filter == "Warm Cinematic":
                    vf_parts.append("colorbalance=rm=0.1:bm=-0.1")
                elif color_filter == "Vintage Film 70s":
                    vf_parts.append("eq=saturation=0.7:contrast=1.1,colorbalance=rm=0.2:gm=0.1")
                elif color_filter == "HDR Vibrant":
                    vf_parts.append("unsharp=3:3:1.5:3:3:0.5")

                if clipchamp_effect == "Cinematic Letterbox (Cinemascope)":
                    vf_parts.append("drawbox=y=0:h=ih/10:color=black:t=fill,drawbox=y=ih-ih/10:h=ih/10:color=black:t=fill")
                elif clipchamp_effect == "Soft Vignette Glow":
                    vf_parts.append("vignette=PI/4")

                vf_parts.append("scale=540:960")
                vf_preview_str = ",".join(vf_parts)

                subprocess.run(
                    f'ffmpeg -y -ss {target_time} -i "{video_path}" -vframes 1 -vf "{vf_preview_str}" "{preview_path}"', 
                    shell=True, capture_output=True
                )
                
                if os.path.exists(preview_path):
                    img = Image.open(preview_path)
                    draw = ImageDraw.Draw(img)
                    
                    if "Hormozi" in style_preset or "Lemon" in style_preset:
                        text_color, outline_color, anim_effect = "#FFFF00", "#000000", "Pop-In Scale"
                    elif "Cyberpunk" in style_preset or "Matrix" in style_preset:
                        text_color, outline_color, anim_effect = "#00FF00", "#000000", "Pop-In Scale"
                    elif "Ocean" in style_preset or "Ice" in style_preset:
                        text_color, outline_color, anim_effect = "#00FFFF", "#000066", "Fade In"
                    elif "Sunset" in style_preset or "Tangerine" in style_preset:
                        text_color, outline_color, anim_effect = "#FF8000", "#000000", "Pop-In Scale"
                    elif "Royal" in style_preset:
                        text_color, outline_color, anim_effect = "#FFD700", "#330000", "Pop-In Scale"
                    elif "Emergency" in style_preset or "Firecracker" in style_preset:
                        text_color, outline_color, anim_effect = "#FF0000", "#FFFFFF", "Standard"
                    else:
                        text_color, outline_color, anim_effect = "#FFFFFF", "#000000", "Fade In"

                    w, h = img.size
                    sample_words = ["CLIPPING", "PREVIEW", "TEXT"]
                    raw_text = " ".join(sample_words[:words_per_line])
                    
                    if "Pop-In" in anim_effect:
                        raw_text = "💥 " + raw_text
                    elif "Fade" in anim_effect:
                        raw_text = "✨ " + raw_text

                    wrapped_lines = textwrap.wrap(raw_text, width=14)
                    wrapped_text = "\n".join(wrapped_lines)

                    # Dynamic pro font loader from fonts.py
                    font = get_pro_font(font_choice, font_size)

                    if "Top" in caption_align:
                        y_pos = int(h * 0.18)
                    elif "Middle-Center" in caption_align:
                        y_pos = int(h * 0.5)
                    else:
                        y_pos = int(h - 260)

                    x_pos = int(w / 2)
                    draw.multiline_text(
                        (x_pos, y_pos), wrapped_text, font=font, fill=text_color, 
                        anchor="mm", align="center", stroke_width=3, stroke_fill=outline_color
                    )
                    st.image(img, width=280, caption=f"Live Preview ({font_choice.split('.')[1].strip()})")

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
                orig_vol_pct = st.slider("Original Voice Volume (%)", min_value=0, max_value=200, value=100, step=5)
                orig_vol = orig_vol_pct / 100.0
            with col_vol2:
                bg_vol_pct = st.slider("Background Music Volume (%)", min_value=0, max_value=100, value=15, step=1)
                bg_vol = bg_vol_pct / 100.0

    if render_clicked:
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

        with st.spinner("Processing High-Quality Professional Shorts..."):
            for clip_num, start_sec, duration_sec in tasks:
                cropped_file = f"cropped_{clip_num}.mp4"
                final_file = f"final_short_{clip_num}.mp4"
                
                render_vf_parts = []
                if enable_face_tracking:
                    f_x = detect_face_center(video_path, start_sec)
                    if f_x:
                        render_vf_parts.append(f"crop=ih*9/16:ih:clamp(x={f_x}-ih*9/32\\,0\\,in_w-ih*9/16):0")
                    else:
                        render_vf_parts.append("crop=ih*9/16:ih")
                else:
                    render_vf_parts.append("crop=ih*9/16:ih")

                if enable_flip:
                    render_vf_parts.append("hflip")
                
                if color_filter == "Cyberpunk Glow":
                    render_vf_parts.append("eq=saturation=1.4:contrast=1.2")
                elif color_filter == "High Contrast":
                    render_vf_parts.append("eq=contrast=1.3:brightness=0.05")
                elif color_filter == "Warm Cinematic":
                    render_vf_parts.append("colorbalance=rm=0.1:bm=-0.1")
                elif color_filter == "Vintage Film 70s":
                    render_vf_parts.append("eq=saturation=0.7:contrast=1.1,colorbalance=rm=0.2:gm=0.1")
                elif color_filter == "HDR Vibrant":
                    render_vf_parts.append("unsharp=3:3:1.5:3:3:0.5")

                if clipchamp_effect == "Cinematic Letterbox (Cinemascope)":
                    render_vf_parts.append("drawbox=y=0:h=ih/10:color=black:t=fill,drawbox=y=ih-ih/10:h=ih/10:color=black:t=fill")
                elif clipchamp_effect == "Soft Vignette Glow":
                    render_vf_parts.append("vignette=PI/4")

                render_vf_parts.append("scale=1080:1920")
                
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
                    align_map = {"Top (Safe Zone)": "6", "Middle-Center": "5", "Bottom (Safe Zone)": "2"}
                    align_val = align_map[caption_align]
                    
                    if "Hormozi" in style_preset or "Lemon" in style_preset:
                        ass_color, anim_tag_type = "&H0000FFFF", "pop"
                    elif "Cyberpunk" in style_preset or "Matrix" in style_preset:
                        ass_color, anim_tag_type = "&H00FF0000", "pop"
                    elif "Ocean" in style_preset or "Ice" in style_preset:
                        ass_color, anim_tag_type = "&H00FFFF00", "fade"
                    elif "Sunset" in style_preset:
                        ass_color, anim_tag_type = "&H000080FF", "pop"
                    elif "Royal" in style_preset:
                        ass_color, anim_tag_type = "&H0000D7FF", "pop"
                    else:
                        ass_color, anim_tag_type = "&H00FFFFFF", "fade"

                    ass_font_name = "Liberation Serif" if any(x in font_choice for x in ["Playfair", "Lora", "Merriweather", "Serif"]) else "Liberation Sans"

                    result = model.transcribe(cropped_file, word_timestamps=True)
                    ass_file = f"subs_{clip_num}.ass"
                    
                    with open(ass_file, "w", encoding="utf-8") as f:
                        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
                        f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                        
                        margin_v_val = 240 if "Bottom" in caption_align else (160 if "Top" in caption_align else 960)
                        
                        f.write(f"Style: Default,{ass_font_name},{font_size*2.2},{ass_color},&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{align_val},108,108,{margin_v_val},1\n\n")
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
                                    
                                    if anim_tag_type == "pop":
                                        anim_tag = r"{\t(0,80,\fscx115\fscy115)\t(80,160,\fscx100\fscy100)}"
                                    elif anim_tag_type == "fade":
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
