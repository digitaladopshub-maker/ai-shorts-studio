import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    # Expanded foolproof font paths available across Linux & Streamlit Cloud containers
    font_pool = [
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
    ]
    
    # Filter only existing files on the server
    available_fonts = [f for f in font_pool if os.path.exists(f)]
    
    if not available_fonts:
        return ImageFont.load_default()

    # Smart mapping based on user selection
    selected_path = available_fonts[0]
    choice_lower = font_choice.lower()
    
    if "impact" in choice_lower:
        for f in available_fonts:
            if "Impact" in f:
                selected_path = f
                break
    elif any(x in choice_lower for x in ["arial", "black", "heavy", "pro", "anton", "bebas", "montserrat", "poppins", "roboto", "ubuntu", "comic", "trebuchet", "oswald", "raleway"]):
        for f in available_fonts:
            if "Arial_Black" in f or "LiberationSans" in f or "DejaVuSans" in f:
                selected_path = f
                break
    elif any(x in choice_lower for x in ["serif", "playfair", "lora", "merriweather", "crimson", "cinzel"]):
        for f in available_fonts:
            if "Serif" in f:
                selected_path = f
                break
    elif any(x in choice_lower for x in ["mono", "code", "jetbrains", "fira", "space"]):
        for f in available_fonts:
            if "Mono" in f:
                selected_path = f
                break

    # Apply scaling factor safely
    final_px = max(int(font_size * 2.2), 12)
    
    try:
        return ImageFont.truetype(selected_path, final_px)
    except Exception:
        try:
            return ImageFont.truetype(available_fonts[0], final_px)
        except Exception:
            return ImageFont.load_default()
