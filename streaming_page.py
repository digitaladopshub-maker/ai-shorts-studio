import os, subprocess, streamlit as st
STREAM_DIR="streaming_uploads"; os.makedirs(STREAM_DIR,exist_ok=True)
def _alive(proc): return proc is not None and proc.poll() is None
def render_streaming_page():
    st.title("📡 Live Streaming Dashboard")
    st.caption("MP4 video ko FFmpeg ke zariye YouTube Live RTMP par stream karein.")
    st.warning("Yeh mode FFmpeg ko isi Streamlit server par chalata hai. Streamlit Community Cloud par app sleep/restart ya resource limits ki wajah se 3–4 ghantay ki reliability guaranteed nahi. Reliable long-running streaming ke liye persistent worker chahiye.")
    proc=st.session_state.get("stream_process")
    if _alive(proc):
        st.success("FFmpeg process chal raha hai.")
        if st.button("⏹ Stop Streaming",type="primary",use_container_width=True):
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill()
            st.session_state.stream_process=None; st.rerun()
    else:
        uploaded=st.file_uploader("MP4 video upload karein",type=["mp4"],key="stream_video")
        server=st.text_input("YouTube Live Server URL",value="rtmp://a.rtmp.youtube.com/live2")
        key=st.text_input("Stream Key",type="password",help="Is key ko private rakhein.")
        hours=st.number_input("Stream duration (hours)",min_value=1,max_value=12,value=4,step=1)
        quality=st.selectbox("Output quality",["1080p","720p","480p"])
        profiles={"1080p":("1920:1080","4500k"),"720p":("1280:720","2500k"),"480p":("854:480","1200k")}
        dims,rate=profiles[quality]
        st.caption(f"{quality} • H.264 video {rate} • AAC audio")
        st.caption("Upload limit config mein 2048 MB hai; hosting platform ki apni limits bhi apply ho sakti hain.")
        if st.button("▶ Start Live Stream",type="primary",use_container_width=True):
            if uploaded is None: st.error("Pehle MP4 video upload karein.")
            elif not server.strip().startswith("rtmp"): st.error("Valid RTMP server URL enter karein.")
            elif not key.strip(): st.error("YouTube Live stream key enter karein.")
            else:
                path=os.path.join(STREAM_DIR,"live_input.mp4")
                with open(path,"wb") as f: f.write(uploaded.getbuffer())
                target=server.rstrip("/")+"/"+key.strip()
                vf=f"scale={dims}:force_original_aspect_ratio=decrease,pad={dims}:(ow-iw)/2:(oh-ih)/2"
                cmd=["ffmpeg","-hide_banner","-loglevel","warning","-re","-stream_loop","-1","-i",path,"-t",str(int(hours*3600)),"-vf",vf,"-r","30","-c:v","libx264","-preset","veryfast","-b:v",rate,"-maxrate",rate,"-bufsize",rate,"-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-ar","44100","-f","flv",target]
                try:
                    st.session_state.stream_process=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    st.success("FFmpeg process start ho gaya. YouTube Studio mein stream status verify karein."); st.rerun()
                except FileNotFoundError: st.error("FFmpeg server par available nahi. packages.txt check karein.")
                except Exception as e: st.error(f"Stream start nahi ho saki: {e}")
    st.markdown("---")
    st.markdown("**Start se pehle:** YouTube Studio se Live Streaming enable karke RTMP server aur stream key lein. Key private rakhein. Uploaded video repeat hogi jab tak selected duration poori na ho.")
