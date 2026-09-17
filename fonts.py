import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    # Default fallback font jo sabse pehle check hoga
    default_font_name = "Impact.ttf"
    default_path = os.path.join(FONT_DIR, default_font_name)
    
    choice_lower = font_choice.lower().strip()
    
    # Exact mapping matching your uploaded files in the fonts folder
    if "impact" in choice_lower:
        selected_file = "Impact.ttf"
    elif "bebas" in choice_lower:
        selected_file = "BebasNeue-Regular.ttf"
    elif "montserrat" in choice_lower:
        selected_file = "Montserrat-VariableFont_wght.ttf"
    elif "roboto" in choice_lower:
        if "bold" in choice_lower:
            selected_file = "Roboto-Bold.ttf"
        else:
            selected_file = "Roboto-Regular.ttf"
    elif "popping" in choice_lower or "cute" in choice_lower:
        selected_file = "Popping-Cute.ttf"
    elif "antonio" in choice_lower:
        selected_file = "AntonioZull-Brush.ttf"
    elif "san antonio" in choice_lower or "charros" in choice_lower:
        selected_file = "San Antonio Charros_personal_use_only.ttf"
    elif "interact" in choice_lower:
        selected_file = "Interact.ttf"
    else:
        selected_file = "Impact.ttf"

    selected_path = os.path.join(FONT_DIR, selected_file)
    
    if not os.path.exists(selected_path):
        if os.path.exists(default_path):
            selected_path = default_path
        else:
            return ImageFont.load_default()

    final_px = max(int(font_size * 2.2), 12)
    
    try:
        return ImageFont.truetype(selected_path, final_px)
    except Exception:
        return ImageFont.load_default()
