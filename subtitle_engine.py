"""Curated viral subtitle presets used by preview and final ASS rendering."""

# Every preset controls typography and visual treatment internally. The UI only
# exposes the master preset, caption position, and words-per-line controls.
SUBTITLE_PRESETS = {
    "Hormozi Bold": {"font": "Impact", "size": 58, "primary": "&H0000FFFF", "text": "#FFFF00", "outline": "#000000", "outline_width": 5, "shadow": 2, "border_style": 1, "bold": True, "italic": False},
    "TikTok Viral": {"font": "Roboto-Bold", "size": 54, "primary": "&H00FFFFFF", "text": "#FFFFFF", "outline": "#111111", "outline_width": 4, "shadow": 2, "border_style": 1, "bold": True, "italic": False},
    "MrBeast Impact": {"font": "Impact", "size": 66, "primary": "&H0000D7FF", "text": "#FFD700", "outline": "#101010", "outline_width": 6, "shadow": 3, "border_style": 1, "bold": True, "italic": False},
    "Podcast Pro": {"font": "Montserrat-VariableFont_wght", "size": 48, "primary": "&H00FFFFFF", "text": "#FFFFFF", "outline": "#171717", "outline_width": 3, "shadow": 1, "border_style": 1, "bold": True, "italic": False},
    "Minimal Clean": {"font": "Roboto-Bold", "size": 46, "primary": "&H00FFFFFF", "text": "#FFFFFF", "outline": "#222222", "outline_width": 2, "shadow": 1, "border_style": 1, "bold": True, "italic": False},
    "Neon Pop": {"font": "Montserrat-VariableFont_wght", "size": 56, "primary": "&H00CCFF00", "text": "#00FFCC", "outline": "#321044", "outline_width": 5, "shadow": 3, "border_style": 1, "bold": True, "italic": False},
    "Cinematic Premium": {"font": "BebasNeue-Regular", "size": 58, "primary": "&H00F2F2F2", "text": "#F2F2F2", "outline": "#171717", "outline_width": 3, "shadow": 2, "border_style": 1, "bold": False, "italic": False},
    "YouTube Shorts Pro": {"font": "Montserrat-VariableFont_wght", "size": 54, "primary": "&H0000FFFF", "text": "#FFFF00", "outline": "#080808", "outline_width": 5, "shadow": 2, "border_style": 1, "bold": True, "italic": False},
    "Gaming Energy": {"font": "Impactbrutas", "size": 62, "primary": "&H0000A5FF", "text": "#FF5A00", "outline": "#080808", "outline_width": 6, "shadow": 3, "border_style": 1, "bold": True, "italic": False},
    "Clean Highlight": {"font": "Interact", "size": 50, "primary": "&H0000E5FF", "text": "#FFE500", "outline": "#161616", "outline_width": 3, "shadow": 1, "border_style": 1, "bold": True, "italic": False},
}

def get_subtitle_preset_config(style_preset):
    """Return a copy of the selected preset's complete visual configuration."""
    return dict(SUBTITLE_PRESETS.get(style_preset, SUBTITLE_PRESETS["Hormozi Bold"]))

def get_subtitle_styling(style_preset):
    """Backward-compatible styling tuple: text, outline, box, animation, ASS color."""
    cfg = get_subtitle_preset_config(style_preset)
    return (cfg["text"], cfg["outline"], False, "Pop-In Scale", cfg["primary"])
