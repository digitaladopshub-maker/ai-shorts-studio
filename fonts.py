import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    # Professional TrueType font mapping for Linux / Streamlit Cloud
    # Fallback to standard robust fonts if specific style not found
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    
    # Specific pool selection based on user choice
    selected_path = font_paths[0]
    if "Impact" in font_choice and os.path.exists("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"):
        selected_path = "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"
    elif "Arial" in font_choice and os.path.exists("/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf"):
        selected_path = "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf"
    elif any(x in font_choice for x in ["Playfair", "Lora", "Merriweather", "Crimson", "Cinzel", "Serif"]):
        for p in [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        ]:
            if os.path.exists(p):
                selected_path = p
                break
    elif any(x in font_choice for x in ["Mono", "Code", "JetBrains", "Fira", "Ubuntu"]):
        for p in [
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        ]:
            if os.path.exists(p):
                selected_path = p
                break
    else:
        for p in font_paths:
            if os.path.exists(p):
                selected_path = p
                break

    try:
        return ImageFont.truetype(selected_path, int(font_size * 1.6))
    except Exception:
        return ImageFont.load_default()
