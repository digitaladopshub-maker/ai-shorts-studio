import os
from PIL import ImageFont

def get_pro_font(font_choice, font_size):
    default_sans = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    default_serif = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
    default_mono = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
    
    choice_lower = font_choice.lower()
    if any(x in choice_lower for x in ["serif", "playfair", "lora", "merriweather", "crimson", "cinzel"]):
        target_path = default_serif if os.path.exists(default_serif) else default_sans
    elif any(x in choice_lower for x in ["mono", "code", "jetbrains", "fira", "ubuntu"]):
        target_path = default_mono if os.path.exists(default_mono) else default_sans
    else:
        target_path = default_sans

    try:
        return ImageFont.truetype(target_path, int(font_size * 1.6))
    except Exception:
        return ImageFont.load_default()

def get_filter_ffmpeg_string(filter_category, filter_name):
    if filter_category == "High Quality & Aesthetic Filters (For Face & Body)":
        if "iPhone HD" in filter_name:
            return "eq=saturation=1.2:contrast=1.1:brightness=0.03,unsharp=5:5:1.0:3:3:0.3"
        elif "HD Glamour" in filter_name:
            return "eq=brightness=0.06:saturation=1.15,gblur=sigma=1.2"
        elif "Flash CCD" in filter_name:
            return "eq=contrast=1.25:saturation=0.85,colorbalance=rm=0.1:gm=0.05"
        elif "Universal Sunset" in filter_name:
            return "colorbalance=rm=0.2:gm=0.05:bm=-0.15,eq=saturation=1.2"
        elif "Bold Glamour" in filter_name:
            return "eq=contrast=1.3:saturation=1.25,unsharp=3:3:1.2"
        elif "Bubblegum" in filter_name:
            return "colorbalance=rm=0.15:bm=0.15,eq=saturation=1.1"
            
    elif filter_category == "🎬 Cinematic & Vibe Filters (For Travel & Vlogs)":
        if "Cinematic Glow" in filter_name:
            return "eq=contrast=1.2:brightness=-0.02:saturation=1.1,unsharp=3:3:0.8"
        elif "Green Lake" in filter_name:
            return "colorbalance=gm=0.2:bm=0.1:rm=-0.1"
        elif "Renoir" in filter_name:
            return "colorbalance=rm=0.15:gm=0.1:bm=-0.2,eq=contrast=1.1"
        elif "Moon Rise" in filter_name:
            return "colorbalance=bm=0.25:rm=-0.1,eq=brightness=-0.05"
        elif "Bad Bunny" in filter_name:
            return "eq=contrast=1.25:saturation=0.9,colorbalance=bm=0.2"
        elif "Cool Vibes" in filter_name:
            return "colorbalance=bm=0.3:rm=-0.15"
            
    elif filter_category == "🤖 Viral AI & Special Effects Filters":
        if "Thermal Effect" in filter_name:
            return "negate,eq=saturation=2.0"
        elif "2016 Filter" in filter_name:
            return "eq=saturation=0.7:contrast=1.1,vignette=PI/3"
        elif "Dreamy Halo" in filter_name:
            return "gblur=sigma=2.5,eq=brightness=0.05"
            
    return ""

def get_style_effect_ffmpeg_string(effect_name):
    if "Cyberpunk" in effect_name:
        return "eq=saturation=1.5:contrast=1.3,colorbalance=rm=0.2:bm=0.3"
    elif "Glitch Portrait" in effect_name:
        return "eq=contrast=1.4:brightness=0.1,unsharp=7:7:2.0"
    elif "Blur / Halo Blur" in effect_name or "Blur" in effect_name:
        return "gblur=sigma=3.0"
    elif "Camera Shake" in effect_name:
        return "crop=in_w-20:in_h-20:10+10*sin(t*20):10+10*cos(t*15)"
    elif "Flash" in effect_name:
        return "eq=brightness='if(lt(mod(t,2),0.2),0.4,0)'"
    elif "Soft Vignette Glow" in effect_name:
        return "vignette=PI/4"
    elif "VHS Glitch" in effect_name:
        return "eq=contrast=1.3:saturation=0.6,noise=alls=20:allf=t+u"
    elif "Cinemascope" in effect_name:
        return "drawbox=y=0:h=ih/10:color=black:t=fill,drawbox=y=ih-ih/10:h=ih/10:color=black:t=fill"
    return ""
