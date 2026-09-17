import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    # Robust font file paths mapping for Linux/Streamlit Cloud
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    
    # Select path based on choice category
    selected_path = paths[0]
    if any(x in font_choice for x in ["Impact", "Arial Black", "Anton", "Bebas", "Black", "Heavy", "Pro"]):
        for p in [
            "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]:
            if os.path.exists(p):
                selected_path = p
                break
    elif any(x in font_choice for x in ["Serif", "Playfair", "Lora", "Merriweather", "Crimson", "Cinzel"]):
        for p in [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        ]:
            if os.path.exists(p):
                selected_path = p
                break
    elif any(x in font_choice for x in ["Mono", "Code", "JetBrains", "Fira", "Space", "Ubuntu"]):
        for p in [
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        ]:
            if os.path.exists(p):
                selected_path = p
                break

    # Dynamic scaling factor fixed so font size is never too small
    calculated_size = max(int(font_size * 2.2), 16)
    try:
        return ImageFont.truetype(selected_path, calculated_size)
    except Exception:
        return ImageFont.load_default()
