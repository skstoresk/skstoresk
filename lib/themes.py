"""Theme system — 4 readable light themes.

- Visitor apni marzi ka theme site header ke 🎨 picker se chun sakta hai
  (choice session me rehti hai).
- Admin portal → Settings me site ka DEFAULT theme set hota hai.
- Sab themes light-based hain taake text hamesha readable rahe
  (Streamlit ke native widgets bhi light theme par hain).
- Keys wahi rakhe hain taake pehle se saved settings na tooten.
"""

THEMES = {
    "dark-gold": {
        "label": "🟡 Golden",
        "accent": "#c9962e",
        "accent_dark": "#a87b1f",
        "accent_soft": "rgba(201,150,46,.14)",
        "accent_border": "rgba(201,150,46,.4)",
        "glow": "rgba(201,150,46,.08)",
    },
    "ocean": {
        "label": "🔵 Ocean Blue",
        "accent": "#2f7fd1",
        "accent_dark": "#1f5fa8",
        "accent_soft": "rgba(47,127,209,.12)",
        "accent_border": "rgba(47,127,209,.4)",
        "glow": "rgba(47,127,209,.07)",
    },
    "emerald": {
        "label": "🟢 Emerald",
        "accent": "#1da862",
        "accent_dark": "#147a45",
        "accent_soft": "rgba(29,168,98,.12)",
        "accent_border": "rgba(29,168,98,.4)",
        "glow": "rgba(29,168,98,.07)",
    },
    "purple": {
        "label": "🟣 Royal Purple",
        "accent": "#8f63e8",
        "accent_dark": "#6d3fd4",
        "accent_soft": "rgba(143,99,232,.12)",
        "accent_border": "rgba(143,99,232,.4)",
        "glow": "rgba(143,99,232,.07)",
    },
}

DEFAULT_THEME = "dark-gold"


def theme_keys():
    return list(THEMES.keys())


def theme_label(key: str) -> str:
    return THEMES.get(key, THEMES[DEFAULT_THEME])["label"]


def theme_vars_css(key: str) -> str:
    """CSS variables for the chosen theme (injected in app.py)."""
    t = THEMES.get(key, THEMES[DEFAULT_THEME])
    return (
        "<style>:root{"
        f"--sk-accent:{t['accent']};"
        f"--sk-accent-dark:{t['accent_dark']};"
        f"--sk-accent-soft:{t['accent_soft']};"
        f"--sk-accent-border:{t['accent_border']};"
        f"--sk-glow:{t['glow']};"
        "}</style>"
    )
