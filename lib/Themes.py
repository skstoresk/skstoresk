"""Theme system — 4 readable dark themes.

- Visitor apni marzi ka theme site header ke 🎨 picker se chun sakta hai
  (choice session me rehti hai).
- Admin portal → Settings me site ka DEFAULT theme set hota hai.
- Sab themes dark-based hain taake text hamesha readable rahe
  (Streamlit ke native widgets bhi dark theme par hain).
"""

THEMES = {
    "dark-gold": {
        "label": "🟡 Dark Gold",
        "accent": "#f5c451",
        "accent_dark": "#d99a1f",
        "accent_soft": "rgba(245,196,81,.18)",
        "accent_border": "rgba(245,196,81,.35)",
        "glow": "rgba(245,196,81,.07)",
    },
    "ocean": {
        "label": "🔵 Ocean Blue",
        "accent": "#4da6ff",
        "accent_dark": "#2f7fd1",
        "accent_soft": "rgba(77,166,255,.16)",
        "accent_border": "rgba(77,166,255,.35)",
        "glow": "rgba(77,166,255,.07)",
    },
    "emerald": {
        "label": "🟢 Emerald",
        "accent": "#2fd27d",
        "accent_dark": "#1da862",
        "accent_soft": "rgba(47,210,125,.16)",
        "accent_border": "rgba(47,210,125,.35)",
        "glow": "rgba(47,210,125,.07)",
    },
    "purple": {
        "label": "🟣 Royal Purple",
        "accent": "#b388ff",
        "accent_dark": "#8f63e8",
        "accent_soft": "rgba(179,136,255,.16)",
        "accent_border": "rgba(179,136,255,.35)",
        "glow": "rgba(179,136,255,.07)",
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
