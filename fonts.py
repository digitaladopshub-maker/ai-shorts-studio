import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    # Check if custom uploaded font exists in the local 'fonts/' folder
    choice_lower = font_choice.lower()
    custom_font_file = None
    
    if "impact" in choice_lower:
        custom_font_file = "Impact.ttf"
    elif "bebas" in choice_lower:
        custom_font_file = "BebasNeue-Regular.ttf"
    elif "montserrat" in choice_lower:
        custom_font_file = "Montserrat-VariableFont_wght.ttf"
    elif "roboto" in choice_lower:
        custom_font_file = "Roboto-Bold.ttf" if "bold" in choice_lower else "Roboto-Regular.ttf"
    elif "popping" in choice_lower:
        custom_font_file = "Popping-Cute.ttf"
    elif "antonio" in choice_lower:
        custom_font_file = "AntonioZull-Brush.ttf"
    elif "san antonio" in choice_lower or "charros" in choice_lower:
        custom_font_file = "San Antonio Charros_personal_use_only.ttf"
    elif "interact" in choice_lower:
        custom_font_file = "Interact.ttf"
        
    if custom_font_file:
        custom_path = os.path.join(FONT_DIR, custom_font_file)
        if os.path.exists(custom_path):
            try:
                return ImageFont.truetype(custom_path, int(font_size * 2.2))
            except Exception:
                pass

    # Fallback to original system font paths if local file is missing
    font_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
    ]
    
    selected_path = font_paths[2]
    
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
