import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    # Aapke upload kiye gaye fonts ki exact file dictionary mapping
    font_map = {
        "impact": "Impact.ttf",
        "bebas neue": "BebasNeue-Regular.ttf",
        "montserrat": "Montserrat-VariableFont_wght.ttf",
        "roboto bold": "Roboto-Bold.ttf",
        "roboto regular": "Roboto-Regular.ttf",
        "popping cute": "Popping-Cute.ttf",
        "antonio zull brush": "AntonioZull-Brush.ttf",
        "san antonio charros": "San Antonio Charros_personal_use_only.ttf",
        "interact": "Interact.ttf"
    }
    
    # Default fallback font agar koi match na ho
    default_font = "Impact.ttf"
    
    choice_lower = font_choice.lower().strip()
    target_filename = default_font
    
    for key, filename in font_map.items():
        if key in choice_lower:
            target_filename = filename
            break
            
    font_path = os.path.join(FONT_DIR, target_filename)
    
    # Agar file nahi milti toh folder ki pehli available .ttf file utha lo
    if not os.path.exists(font_path):
        if os.path.exists(FONT_DIR):
            files = [f for f in os.listdir(FONT_DIR) if f.endswith(".ttf")]
            if files:
                font_path = os.path.join(FONT_DIR, files[0])
            else:
                return ImageFont.load_default()
        else:
            return ImageFont.load_default()

    # Font size scaling (Medium = 24px default)
    final_px = max(int(font_size * 2.0), 12)
    
    try:
        return ImageFont.truetype(font_path, final_px)
    except Exception:
        return ImageFont.load_default()
