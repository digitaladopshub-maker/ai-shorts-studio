import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    
    # Map user choices to uploaded files
    font_map = {
        "impact": "Impact.ttf",
        "bebas": "BebasNeue-Regular.ttf",
        "montserrat": "Montserrat-VariableFont_wght.ttf",
        "roboto bold": "Roboto-Bold.ttf",
        "roboto regular": "Roboto-Regular.ttf",
        "popping": "Popping-Cute.ttf",
        "antonio": "AntonioZull-Brush.ttf",
        "san antonio": "San Antonio Charros_personal_use_only.ttf",
        "interact": "Interact.ttf"
    }
    
    choice_lower = font_choice.lower().strip()
    target_filename = "Impact.ttf" # Default
    
    for key, filename in font_map.items():
        if key in choice_lower:
            target_filename = filename
            break
            
    font_path = os.path.join(FONT_DIR, target_filename)
    
    # Agar specific file nahi milti toh folder ki koi bhi .ttf file utha lo
    if not os.path.exists(font_path) and os.path.exists(FONT_DIR):
        files = [f for f in os.listdir(FONT_DIR) if f.endswith(".ttf")]
        if files:
            font_path = os.path.join(FONT_DIR, files[0])

    # Pro Shorts ke liye bada aur bold font size multiplier (Medium = 45px+, Large = 60px+)
    final_px = max(int(font_size * 1.8), 36)
    
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, final_px)
        except Exception:
            pass
            
    # Agar phir bhi load na ho toh Pillow ka default load karne ke bajaye ek safe size return karein
    return ImageFont.load_default()
