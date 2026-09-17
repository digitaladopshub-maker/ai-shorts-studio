import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    # Base fallback paths available on Linux / Streamlit Cloud
    default_sans = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    default_serif = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
    default_mono = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
    
    # Specific font family routing for all 50 options to ensure visible real-time changes
    choice_lower = font_choice.lower()
    
    if any(x in choice_lower for x in ["serif", "playfair", "lora", "merriweather", "crimson", "cinzel"]):
        target_path = default_serif
        if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"):
            target_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    elif any(x in choice_lower for x in ["mono", "code", "jetbrains", "fira", "ubuntu"]):
        target_path = default_mono
        if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"):
            target_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    elif any(x in choice_lower for x in ["comic", "caveat", "pacifico", "lobster", "sriracha", "shadows", "bangers", "fredoka"]):
        # Hand/Casual style fallback to available sans/display
        target_path = default_sans
    elif any(x in choice_lower for x in ["impact", "arial black", "anton", "bebas", "archivo", "bungee"]):
        # Heavy viral display headers
        if os.path.exists("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"):
            target_path = "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"
        elif os.path.exists("/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf"):
            target_path = "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf"
        else:
            target_path = default_sans
    else:
        target_path = default_sans
        if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            target_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    try:
        return ImageFont.truetype(target_path, int(font_size * 1.6))
    except Exception:
        return ImageFont.load_default()
