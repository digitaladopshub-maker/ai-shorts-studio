import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    choice_lower = font_choice.lower()
    custom_font_file = None
    
    # 15o fonts ki proper mapping screenshot ke mutabiq
    if "antonio zull" in choice_lower:
        custom_font_file = "AntonioZull-Brush.ttf"
    elif "bebas neue" in choice_lower:
        custom_font_file = "BebasNeue-Regular.ttf"
    elif "impact club" in choice_lower:
        custom_font_file = "Impact Club.ttf"
    elif choice_lower == "impact" or "impact standard" in choice_lower:
        custom_font_file = "Impact.ttf"
    elif "impact brutas" in choice_lower:
        custom_font_file = "Impactbrutas.ttf"
    elif choice_lower == "impacted":
        custom_font_file = "IMPACTED.ttf"
    elif "impacted 2.0" in choice_lower:
        custom_font_file = "Impacted2.0.ttf"
    elif "impact extravagant" in choice_lower:
        custom_font_file = "Impact-Extravagant.ttf"
    elif "interact" in choice_lower:
        custom_font_file = "Interact.ttf"
    elif "montserrat italic" in choice_lower:
        custom_font_file = "Montserrat-Italic-VariableFont_wght.ttf"
    elif "montserrat" in choice_lower:
        custom_font_file = "Montserrat-VariableFont_wght.ttf"
    elif "popping cute" in choice_lower:
        custom_font_file = "Popping-Cute.ttf"
    elif "roboto bold" in choice_lower:
        custom_font_file = "Roboto-Bold.ttf"
    elif "roboto" in choice_lower:
        custom_font_file = "Roboto-Regular.ttf"
    elif "san antonio charros" in choice_lower:
        custom_font_file = "San Antonio Charros_personal_use_only.ttf"
        
    if custom_font_file:
        custom_path = os.path.join(FONT_DIR, custom_font_file)
        if os.path.exists(custom_path):
            try:
                return ImageFont.truetype(custom_path, int(font_size * 2.2))
            except Exception:
                pass

    # Fallback default font agar koi file missing ho
    fallback_path = os.path.join(FONT_DIR, "Impact.ttf")
    if not os.path.exists(fallback_path):
        fallback_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    final_px = int(font_size * 2.2)
    try:
        return ImageFont.truetype(fallback_path, final_px)
    except Exception:
        return ImageFont.load_default()
