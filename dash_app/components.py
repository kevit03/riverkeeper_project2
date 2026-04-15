"""Small UI primitives used throughout the Dash layout."""

from __future__ import annotations

from dash import html
import dash_bootstrap_components as dbc


def kpi_tile(label: str, value: str, hint: str | None = None, variant: str = "primary") -> html.Div:
    """A branded KPI tile with gradient accent bar."""
    classes = "kpi"
    if variant == "green":
        classes += " kpi--green"
    elif variant == "amber":
        classes += " kpi--amber"
    elif variant == "teal":
        classes += " kpi--teal"

    children = [
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value"),
    ]
    if hint:
        children.append(html.Div(hint, className="kpi-hint"))
    return html.Div(children, className=classes)


def chart_card(title: str, figure_component, subtitle: str | None = None) -> html.Div:
    """Wrap a dcc.Graph (or any component) in a styled card."""
    kids = [html.H4(title, className="chart-card-title")]
    if subtitle:
        kids.append(html.P(subtitle, className="chart-card-sub"))
    kids.append(figure_component)
    return html.Div(kids, className="chart-card fade-up")


def section_heading(title: str, subtitle: str | None = None) -> html.Div:
    return html.Div(
        [
            html.Span(title),
            html.Span(subtitle or "", className="section-sub") if subtitle else None,
        ],
        className="section-heading",
    )


def empty_state(text: str, icon: str | None = None) -> html.Div:
    """Empty state featuring the Riverkeeper logo as a watermark."""
    children = [
        html.Img(src="/assets/RKlogo.png", className="empty-state-logo"),
        html.Div(text, className="empty-state-text"),
    ]
    if icon:
        children.insert(0, html.Div(icon, style={"fontSize": "36px", "marginBottom": "8px", "opacity": 0.6}))
    return html.Div(children, className="empty-state fade-up")


def info_alert(message: str, kind: str = "info") -> dbc.Alert:
    return dbc.Alert(message, color=kind, className="fade-up")
