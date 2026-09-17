def get_subtitle_styling(style_preset):
    preset_lower = style_preset.lower()
    
    if "hormozi" in preset_lower or "pop" in preset_lower or "neon" in preset_lower:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
    elif "minimal" in preset_lower or "apple" in preset_lower or "real estate" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Fade In", "&H00FFFFFF")
    elif "gradient" in preset_lower or "3d" in preset_lower:
        return ("#00FFFF", "#000066", False, "Pop-In Scale", "&H00FFFF00")
    elif "alert" in preset_lower or "firecracker" in preset_lower:
        return ("#FF0000", "#FFFFFF", False, "Standard", "&H000000FF")
    elif "cyberpunk" in preset_lower:
        return ("#00FF00", "#000000", True, "Pop-In Scale", "&H00FF0000")
    elif "karaoke" in preset_lower:
        return ("#FFD700", "#000000", False, "Pop-In Scale", "&H0000D7FF")
    else:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
