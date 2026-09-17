def get_subtitle_styling(style_preset):
    # Mapping based on user's exact categorized subtitle presets
    preset_lower = style_preset.lower()
    
    # 1. Word-by-Word Pop & Highlight Styles
    if "hormozi style" in preset_lower:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
    elif "border pop-up" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Standard", "&H00FFFFFF")
    elif "karaoke highlight" in preset_lower:
        return ("#00FFCC", "#000000", False, "Pop-In Scale", "&H00CCFF00")
    elif "power word scale" in preset_lower:
        return ("#FFFF33", "#000000", False, "Pop-In Scale", "&H0033FFFF")
    elif "glow & shine effect" in preset_lower:
        return ("#00FFFF", "#000000", False, "Fade In", "&H00FFFF00")
        
    # 2. Modern & Aesthetic Subtitle Blocks
    elif "minimal subtitle block" in preset_lower:
        return ("#FFFFFF", "#333333", True, "Standard", "&H00FFFFFF")
    elif "apple style minimal" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Fade In", "&H00FFFFFF")
    elif "gradient premium stack" in preset_lower:
        return ("#00D4FF", "#000066", False, "Pop-In Scale", "&H00FFD400")
    elif "real estate pro" in preset_lower:
        return ("#FFFFFF", "#111111", False, "Standard", "&H00FFFFFF")
    elif "3d viral text" in preset_lower:
        return ("#FFD700", "#330000", False, "Pop-In Scale", "&H0000D7FF")
        
    # 3. Animated & Dynamic Transitions (Motion Captions)
    elif "slide up" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Fade In", "&H00FFFFFF")
    elif "typewriter effect" in preset_lower:
        return ("#00FF00", "#000000", False, "Standard", "&H0000FF00")
    elif "flicker text" in preset_lower:
        return ("#FF33CC", "#000000", False, "Pop-In Scale", "&H00CC33FF")
    elif "wave in / bounce" in preset_lower:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
    elif "blur fade in" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Fade In", "&H00FFFFFF")
        
    # 4. Social Media Icons & Auto Emoji Captions
    elif "auto-emoji pop" in preset_lower:
        return ("#FF5733", "#000000", False, "Pop-In Scale", "&H003357FF")
    elif "tiktok classic style" in preset_lower:
        return ("#FFFFFF", "#000000", False, "Standard", "&H00FFFFFF")
    elif "sound effects bracket" in preset_lower:
        return ("#FFFF66", "#000000", False, "Standard", "&H0066FFFF")
    elif "capcut auto lyric template" in preset_lower:
        return ("#FF99FF", "#000000", False, "Fade In", "&H00FF99FF")
    elif "cyberpunk neon" in preset_lower:
        return ("#00FFEF", "#FF007F", False, "Pop-In Scale", "&H00EFFF00")
        
    else:
        return ("#FFFF00", "#000000", False, "Pop-In Scale", "&H0000FFFF")
