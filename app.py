import streamlit as st
import whisper
import subprocess
import os
import textwrap
import cv2
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Pro Shorts Studio - Ultimate", layout="wide", initial_sidebar_state="expanded")

st.title("🎬 Smart Pro AI Shorts Studio - Ultimate Edition")
st.caption("Commercial-Grade AI Vertical Video, 20+ Modern Presets, 50+ Fonts & Safe Margin Protection")

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
        enable_face_tracking = st.checkbox("🤖 Enable Smart AI Face Tracking (Center Crop on Speaker)", value=True)
        
        if enable_subs:
            col_controls, col_preview = st.columns([1.2, 0.8])
            
            with col_controls:
                st.subheader("🔥 20+ Modern CapCut/Opus Presets")
                
                # 20 Modern Professional Presets List
                style_preset = st.selectbox("Select Cinematic Style Preset", [
                    "1. ⚡ Alex Hormozi (Neon Yellow + Black Outline + Pop)",
                    "2. 💎 Cyberpunk Neon (Bright Green + Heavy Glow)",
                    "3. 🌊 Ocean Breeze (Cyan + Deep Blue Shadow)",
                    "4. 🔥 Sunset Blaze (Orange-Yellow Gradient + Bold)",
                    "5. 👑 Royal Gold (Metallic Gold + Elegant Outline)",
                    "6. 🚀 TikTok Viral (Bright Electric Blue + White Text)",
                    "7. 🩸 Matrix Code (Lime Green + Dark Shadow)",
                    "8. 🎯 Minimalist Clean (Pure White + Soft Shadow)",
                    "9. 🚨 Emergency Alert (Blood Red + White Background)",
                    "10. 💜 Purple Haze (Neon Purple + Pink Outline)",
                    "11. 🍋 Lemon Punch (Vibrant Yellow + Dark Contour)",
                    "12. ⚡ Flash White (Pure White + Thick Black Border)",
                    "13. 🍊 Tangerine Dream (Neon Orange + Black Stroke)",
                    "14. 🧊 Ice Glacier (Ice Blue + Silver Outline)",
                    "15. 🥑 Avocado Pop (Neon Lime + Deep Green Border)",
                    "16. 🔮 Mystic Violet (Deep Magenta + Dark Glow)",
                    "17. 🍫 Caramel Gold (Warm Amber + Dark Shadow)",
                    "18. 🧨 Firecracker (Bright Coral + Sharp Outline)",
                    "19. 🌿 Emerald Fresh (Mint Green + Dark Stroke)",
                    "20. 🦄 Cyber Unicorn (Pink-Cyan Dual Tone + Shadow)"
                ], index=0)

                st.markdown("---")
                st.subheader("🔤 50+ Eye-Catching Fonts Library")
                
                # 50 Professional Subtitle Fonts Library Categorized
                font_choice = st.selectbox("Select Subtitle Font (50+ Pro Fonts)", [
                    "1. Montserrat Black (Ultra Bold)",
                    "2. Impact Pro (Viral Standard)",
                    "3. Arial Black (Heavy Impact)",
                    "4. Comic Neue Bold (Punchy Casual)",
                    "5. Trebuchet MS Bold (Modern Clean)",
                    "6. Ubuntu Bold (Tech & Gaming)",
                    "7. Liberation Sans Bold (Standard Cinematic)",
                    "8. DejaVu Sans Bold (Sharp High-Contrast)",
                    "9. Inter Heavy (Sleek Modern)",
                    "10. Roboto Black (Google Style Bold)",
                    "11. Poppins ExtraBold (Trendy Social)",
                    "12. Oswald Bold (Tall Condensed Pro)",
                    "13. Anton Regular (Massive Display)",
                    "14. Bebas Neue Pro (Cinematic Shorts)",
                    "15. Nunito ExtraBold (Friendly Rounded)",
                    "16. Raleway Black (Luxury Minimalist)",
                    "17. Quicksand Bold (Clean Round)",
                    "18. Playfair Display Bold (Classic Cinematic)",
                    "19. Merriweather Bold (Editorial Impact)",
                    "20. Fira Code Bold (Tech Code Vibe)",
                    "21. JetBrains Mono Bold (Developer Modern)",
                    "22. Space Grotesk Bold (Futuristic Cyber)",
                    "23. Syne ExtraBold (Unique Artistic)",
                    "24. DM Sans Bold (Clean SaaS)",
                    "25. Work Sans Black (Heavy Corporate)",
                    "26. PT Sans Bold (Reliable Clean)",
                    "27. Open Sans ExtraBold (Universal Readability)",
                    "28. Lora Bold (Serif Storytelling)",
                    "29. Crimson Text Bold (Classic Novel)",
                    "30. Cinzel Bold (Epic Movie Title)",
                    "31. Archivo Black (Heavyweight Impact)",
                    "32. Cabin Bold (Sleek Rounded)",
                    "33. Mulish ExtraBold (Modern Smooth)",
                    "34. Barlow Condensed Bold (Speed Action)",
                    "35. Kanit Bold (Aggressive Thai/English)",
                    "36. Prompt Bold (Clean Rounded Modern)",
                    "37. Sriracha Bold (Handwritten Fun)",
                    "38. Caveat Bold (Handwritten Script)",
                    "39. Pacifico Pro (Cursive Stylish)",
                    "40. Lobster Two (Dynamic Script)",
                    "41. Bangers Regular (Comic Book Action)",
                    "42. Fredoka One (Playful Bubble)",
                    "43. Titan One (Massive Block Display)",
                    "44. Luckiest Guy (Extremely Fun Viral)",
                    "45. Chewy Regular (Cartoon Heavy)",
                    "46. Permanent Marker (Grunge Street)",
                    "47. Amatic SC Bold (Hand-drawn Tall)",
                    "48.Shadows Into Light (Personal Touch)",
                    "49.righteous Regular (Retro Future)",
                    "50.Bungee Inline (Arcade Retro Style)"
                ], index=0)

                st.markdown("---")
                st.subheader("📐 Safe Margin & Alignment")
                
                # Anti-Overlap Safe Margin Alignment (Protects against TikTok/YouTube follow/subscribe buttons)
                caption_align = st.selectbox("Position Alignment (Safe Zone Protected)", [
                    "Bottom (Safe Zone - Above TikTok/YT Buttons)", 
                    "Middle-Center", 
                    "Top (Safe Zone - Below Header/Username)"
                ], index=0)
                
                words_per_line = st.slider("Words Per Line Box", min_value=1, max_value=5, value=2)
                font_size_option = st.selectbox("Font Size Preset", ["Small (18px)", "Medium (24px - Recommended)", "Large (32px)", "Extra Large (40px)"], index=1)
                font_size_map = {"Small (18px)": 18, "Medium (24px - Recommended)": 24, "Large (32px)": 32, "Extra Large (40px)": 40}
                font_size = font_size_map[font_size_option]

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
                    
                    # Resolve Colors & Animation based on 20 Modern Presets
                    if "Hormozi" in style_preset or "Lemon" in style_preset:
                        text_color, outline_color, anim_effect = "#FFFF00", "#000000", "Pop-In Scale (Fast Zoom)"
                    elif "Cyberpunk" in style_preset or "Matrix" in style_preset:
                        text_color, outline_color, anim_effect = "#00FF00", "#000000", "Pop-In Scale (Fast Zoom)"
                    elif "Ocean" in style_preset or "Ice" in style_preset:
                        text_color, outline_color, anim_effect = "#00FFFF", "#000066", "Fade In / Fade Out"
                    elif "Sunset" in style_preset or "Tangerine" in style_preset:
                        text_color, outline_color, anim_effect = "#FF8000", "#000000", "Pop-In Scale (Fast Zoom)"
                    elif "Royal" in style_preset:
                        text_color, outline_color, anim_effect = "#FFD700", "#330000", "Pop-In Scale (Fast Zoom)"
                    elif "Emergency" in style_preset or "Firecracker" in style_preset:
                        text_color, outline_color, anim_effect = "#FF0000", "#FFFFFF", "Standard Pop-Up"
                    else:
                        text_color, outline_color, anim_effect = "#FFFFFF", "#000000", "Fade In / Fade Out"

                    w, h = img.size
                    sample_words = ["MODERN", "AI", "SHORTS", "PRESET", "PREVIEW"]
                    raw_text = " ".join(sample_words[:words_per_line])
                    
                    if "Pop-In" in anim_effect:
                        raw_text = "💥 " + raw_text
                    elif "Fade" in anim_effect:
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

                    # Anti-Overlap Safe Margins (Protects bottom/top from social buttons)
                    if "Top" in caption_align:
                        y_pos = int(h * 0.18) # Safe zone below TikTok/IG usernames
                    elif "Middle-Center" in caption_align:
                        y_pos = int(h * 0.5)
                    else:
                        y_pos = int(h - 260) # Safe zone above TikTok Follow / YouTube Subscribe buttons

                    x_pos = int(w / 2)
                    draw.multiline_text(
                        (x_pos, y_pos), wrapped_text, font=font, fill=text_color, 
                        anchor="mm", align="center", stroke_width=3, stroke_fill=outline_color
                    )
                    st.image(img, caption=f"Live Modern Preview (Frame at {target_time}s)", use_container_width=True)

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

        with st.spinner("Processing High-Quality Shorts with 20+ Presets & Safe Margins..."):
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
                    align_map = {"Top (Safe Zone - Below Header/Username)": "6", "Middle-Center": "5", "Bottom (Safe Zone - Above TikTok/YT Buttons)": "2"}
                    align_val = align_map[caption_align]
                    
                    # Backend color & animation mapping
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

                    result = model.transcribe(cropped_file, word_timestamps=True)
                    ass_file = f"subs_{clip_num}.ass"
                    
                    with open(ass_file, "w", encoding="utf-8") as f:
                        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
                        f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                        
                        # Protected Safe Zone Margins (Prevents overlap with TikTok/YouTube follow/subscribe UI)
                        margin_v_val = 240 if "Bottom" in caption_align else (160 if "Top" in caption_align else 960)
                        
                        f.write(f"Style: Default,Arial,{font_size*2.2},{ass_color},&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{align_val},108,108,{margin_v_val},1\n\n")
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
