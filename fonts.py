import os
from PIL import ImageFont

def get_font_family(font_choice):
    # Dropdown choice ko clean font identifier mein map karna
    font_map = {
        "AntonioZull-Brush": "AntonioZull-Brush",
        "BebasNeue-Regular": "BebasNeue-Regular",
        "Impact Club": "Impact Club",
        "Impact": "Impact",
        "Impactbrutas": "Impactbrutas",
        "IMPACTED": "IMPACTED",
        "Impacted2.0": "Impacted2.0",
        "Impact-Extravagant": "Impact-Extravagant",
        "Interact": "Interact",
        "Montserrat-Italic-VariableFont_wght": "Montserrat-Italic-VariableFont_wght",
        "Montserrat-VariableFont_wght": "Montserrat-VariableFont_wght",
        "Popping-Cute": "Popping-Cute",
        "Roboto-Bold": "Roboto-Bold",
        "Roboto-Regular": "Roboto-Regular",
        "San Antonio Charros_personal_use_only": "San Antonio Charros_personal_use_only"
    }
    return font_map.get(font_choice, "Impact")

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    custom_font_file = font_choice if font_choice.endswith(".ttf") else font_choice + ".ttf"
    custom_path = os.path.join(FONT_DIR, custom_font_file)
    
    if os.path.exists(custom_path):
        try:
            return ImageFont.truetype(custom_path, int(font_size * 2.2))
        except Exception:
            pass

    fallback_path = os.path.join(FONT_DIR, "Impact.ttf")
    if not os.path.exists(fallback_path):
        fallback_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    final_px = int(font_size * 2.2)
    try:
        return ImageFont.truetype(fallback_path, final_px)
    except Exception:
        return ImageFont.load_default()
