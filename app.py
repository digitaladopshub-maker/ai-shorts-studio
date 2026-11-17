import streamlit as st
st.set_page_config(page_title="AI Shorts Studio", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>.block-container{padding-top:2rem;max-width:1200px}.hero{padding:1.4rem 1.6rem;border-radius:18px;background:linear-gradient(120deg,#111827,#334155);color:white;margin-bottom:1rem}.hero h1{margin:0;font-size:2rem}.hero p{margin:.45rem 0 0;color:#d1d5db}div.stButton>button{border-radius:10px;font-weight:650;min-height:3rem}</style>""",unsafe_allow_html=True)
if "active_page" not in st.session_state: st.session_state.active_page="Home"
st.markdown('<div class="hero"><h1>🎬 AI Shorts Studio</h1><p>Clipping aur Live Streaming — dono tools ek hi dashboard mein.</p></div>',unsafe_allow_html=True)
if st.session_state.active_page=="Home":
    st.subheader("Apna tool select karein")
    c1,c2=st.columns(2,gap="large")
    with c1:
        st.markdown("### ✂️ Clipping Studio"); st.write("Long video upload karein, highlights banayein, AI subtitles aur export gallery use karein.")
        if st.button("Open Clipping Studio",use_container_width=True): st.session_state.active_page="Clipping"; st.rerun()
    with c2:
        st.markdown("### 📡 Live Streaming"); st.write("Video file, YouTube Live RTMP settings, stream duration aur FFmpeg controls.")
        if st.button("Open Live Streaming",use_container_width=True): st.session_state.active_page="Live Streaming"; st.rerun()
elif st.session_state.active_page=="Clipping":
    if st.button("← Home"): st.session_state.active_page="Home"; st.rerun()
    from clipping_page import render_clipping_page
    render_clipping_page()
else:
    if st.button("← Home"): st.session_state.active_page="Home"; st.rerun()
    from streaming_page import render_streaming_page
    render_streaming_page()
