"""Design tokens and a shared Plotly template for the Riverkeeper Dash app."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio


# ---- Brand palette — pulled from the Riverkeeper logo -----------------------
COLORS = {
    "bg": "#EAF5F1",
    "surface": "#FFFFFF",
    "surface_alt": "#F3FAF7",
    "border": "#D5E7DD",
    "text": "#0F2B2E",
    "text_muted": "#4D6D6A",
    "text_dim": "#85A19C",
    # Brand
    "primary": "#1D8DC0",        # river blue
    "primary_dark": "#0C567A",
    "accent": "#3FA54A",         # leaf green
    "accent_dark": "#236A2B",
    "accent_light": "#6DC96C",
    "teal": "#4EC3E3",           # highlight blue
    "mint": "#6DC96C",           # highlight green
    "warning": "#F59E0B",
    "danger": "#DC2626",
    "success": "#10B981",
}

# Chart color sequence — blues/greens lead, then warm accents for variety
CHART_COLORS = [
    "#1D8DC0",  # river blue
    "#3FA54A",  # leaf green
    "#4EC3E3",  # light blue
    "#6DC96C",  # mint green
    "#0C567A",  # deep blue
    "#236A2B",  # deep green
    "#F59E0B",  # amber
    "#E11D48",  # rose
    "#7C3AED",  # violet
    "#85A19C",  # sage
]


def build_template() -> None:
    """Register a custom Plotly template named 'riverkeeper'."""
    template = go.layout.Template()

    template.layout = go.Layout(
        font=dict(
            family='"Inter", "Segoe UI", system-ui, -apple-system, sans-serif',
            size=13,
            color=COLORS["text"],
        ),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        colorway=CHART_COLORS,
        margin=dict(l=48, r=24, t=56, b=48),
        title=dict(
            font=dict(size=16, color=COLORS["text"], weight=600),
            x=0.02,
            xanchor="left",
            y=0.96,
            pad=dict(t=8, b=8),
        ),
        hoverlabel=dict(
            bgcolor=COLORS["text"],
            font=dict(color="#FFFFFF", size=12, family='"Inter", system-ui, sans-serif'),
            bordercolor=COLORS["text"],
        ),
        xaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            zerolinecolor=COLORS["border"],
            tickfont=dict(color=COLORS["text_muted"], size=12),
            title=dict(font=dict(color=COLORS["text_muted"], size=13)),
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            zerolinecolor=COLORS["border"],
            tickfont=dict(color=COLORS["text_muted"], size=12),
            title=dict(font=dict(color=COLORS["text_muted"], size=13)),
            showgrid=True,
            gridwidth=1,
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            bordercolor=COLORS["border"],
            borderwidth=0,
            font=dict(color=COLORS["text_muted"], size=12),
        ),
    )

    pio.templates["riverkeeper"] = template
    pio.templates.default = "riverkeeper"


# Apply on import so any chart made anywhere uses the theme
build_template()
