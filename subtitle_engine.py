def get_subtitle_styling(style_preset):
    # Returns (text_color, outline_color, has_box, anim_type, ass_color_hex)
    preset_lower = style_preset.lower()
    
    if "hormozi" in preset_lower:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
    elif "border pop-up" in preset_lower:
        return ("#FFFFFF", "#FF0000", True, "Pop-In Scale", "&H00FFFFFF")
    elif "karaoke highlight" in preset_lower:
        return ("#FFD700", "#000080", False, "Pop-In Scale", "&H0000D7FF")
    elif "power word scale" in preset_lower:
        return ("#00FFFF", "#000000", False, "Pop-In Scale", "&H00FFFF00")
    elif "glow & shine" in preset_lower:
        return ("#FF69B4", "#4B0082", False, "Fade In", "&H00B469FF")
    elif "minimal subtitle block" in preset_lower:
        return ("#FFFFFF", "#333333", True, "Standard", "&H00FFFFFF")
    elif "apple style minimal" in preset_lower:
        return ("#F5F5F5", "#111111", False, "Fade In", "&H00F5F5F5")
    elif "gradient premium stack" in preset_lower:
        return ("#00CED1", "#191970", False, "Pop-In Scale", "&H00D1CE00")
    elif "real estate pro" in preset_lower:
        return ("#FFD700", "#1C1C1C", True, "Standard", "&H0000D7FF")
    elif "3d viral text" in preset_lower:
        return ("#FF4500", "#000000", False, "Pop-In Scale", "&H000045FF")
    elif "multiple word slide up" in preset_lower:
        return ("#ADFF2F", "#006400", False, "Slide Up", "&H002FFFAD")
    elif "typewriter effect" in preset_lower:
        return ("#00FF7F", "#2F4F4F", False, "Standard", "&H007FFF00")
    elif "flicker text" in preset_lower:
        return ("#FF1493", "#000000", False, "Flicker", "&H009314FF")
    elif "wave in" in preset_lower or "bounce" in preset_lower:
        return ("#00BFFF", "#00008B", False, "Bounce", "&H00FFBF00")
    elif "blur fade in" in preset_lower:
        return ("#E0FFFF", "#2F4F4F", False, "Fade In", "&H00FFE0E0")
    elif "auto-emoji pop" in preset_lower:
        return ("#FFD700", "#FF4500", False, "Pop-In Scale", "&H0000D7FF")
    elif "tiktok classic style" in preset_lower:
        return ("#FFFFFF", "#000000", True, "Standard", "&H00FFFFFF")
    elif "sound effects bracket" in preset_lower:
        return ("#00FF00", "#8B0000", False, "Standard", "&H0000FF00")
    elif "capcut auto lyric template" in preset_lower:
        return ("#FF8C00", "#FFFFFF", False, "Pop-In Scale", "&H00008CFF")
    elif "cyberpunk neon" in preset_lower:
        return ("#00FFCC", "#FF00FF", True, "Pop-In Scale", "&H00CCFF00")
    else:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
