import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    font_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
    ]
    
    selected_path = font_paths[2]
    choice_lower = font_choice.lower()
    
    if "impact" in choice_lower and os.path.exists(font_paths[0]):
        selected_path = font_paths[0]
    elif any(x in choice_lower for x in ["arial", "black", "heavy", "pro", "anton", "bebas", "montserrat", "poppins", "roboto"]) and os.path.exists(font_paths[1]):
        selected_path = font_paths[1]
    elif any(x in choice_lower for x in ["serif", "playfair", "lora", "merriweather", "crimson", "cinzel"]):
        for p in font_paths:
            if "Serif" in p and os.path.exists(p):
                selected_path = p
                break
    elif any(x in choice_lower for x in ["mono", "code", "jetbrains", "fira", "space", "ubuntu"]):
        for p in font_paths:
            if "Mono" in p and os.path.exists(p):
                selected_path = p
                break

    final_px = int(font_size * 2.2)
    try:
        return ImageFont.truetype(selected_path, final_px)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", final_px)
        except Exception:
            return ImageFont.load_default()
