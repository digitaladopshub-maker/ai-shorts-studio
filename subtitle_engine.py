def get_subtitle_styling(style_preset):
    # Categorized matching for user's detailed subtitle presets
    preset_lower = style_preset.lower()
    
    if any(x in preset_lower for x in ["hormozi", "border pop", "power word", "glow & shine", "karaoke"]):
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
    elif any(x in preset_lower for x in ["minimal", "apple style", "real estate", "gradient premium"]):
        return ("#FFFFFF", "#000000", False, "Fade In", "&H00FFFFFF")
    elif any(x in preset_lower for x in ["3d viral", "cyberpunk", "glitch"]):
        return ("#00FFFF", "#000066", False, "Pop-In Scale", "&H00FFFF00")
    elif any(x in preset_lower for x in ["slide up", "typewriter", "flicker", "wave", "blur fade"]):
        return ("#FFD700", "#000000", False, "Pop-In Scale", "&H0000D7FF")
    elif any(x in preset_lower for x in ["emoji", "tiktok", "sound effects", "lyric"]):
        return ("#FF5733", "#000000", False, "Standard", "&H003357FF")
    else:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
