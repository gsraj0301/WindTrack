"""Shared UI primitives for the WindTrack dashboard.

One small module so the Asset and Power pages stay visually consistent:
semantic status chips, KPI cards, the unified page header, and a common
Plotly layout. All styling is scoped under the .wt_ prefix.
"""
import streamlit as st
from datetime import datetime

FONT = "Inter, system-ui, 'Segoe UI', sans-serif"

# Semantic color tokens (sky-light theme)
COLORS = {
    'ok':   '#16A34A',
    'warn': '#D97706',
    'crit': '#DC2626',
    'ink':  '#1A2332',
    'muted': '#5B6470',
    'grid': 'rgba(26,35,50,0.08)',
}

CSS = f"""
<style>
html, body, [data-testid="stAppViewContainer"],
[data-testid="stSidebar"], .stApp {{
    font-family: {FONT};
}}

.wt_card {{
    background: #FFFFFF;
    border: 1px solid rgba(26,35,50,0.08);
    border-radius: 10px;
    padding: 12px 14px;
}}
.wt_card .k {{
    font-size: 12px;
    color: {COLORS['muted']};
    margin-bottom: 4px;
}}
.wt_card .v {{
    font-size: 24px;
    font-weight: 650;
    color: {COLORS['ink']};
    line-height: 1.1;
}}
.wt_card .d {{
    font-size: 12px;
    margin-top: 4px;
    font-weight: 600;
}}
.wt_card .ut {{ margin-top: 3px; font-size: 11px; color: #6B7280; }}

.wt_chip {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 11px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.7;
}}
.wt_chip.ok  {{ background: rgba(22,163,74,0.12); color: {COLORS['ok']}; }}
.wt_chip.warn {{ background: rgba(217,119,6,0.14); color: {COLORS['warn']}; }}
.wt_chip.crit {{ background: rgba(220,38,38,0.12);  color: {COLORS['crit']}; }}

.wt_dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; }}
.wt_dot.ok  {{ background: {COLORS['ok']}; }}
.wt_dot.warn {{ background: {COLORS['warn']}; }}
.wt_dot.crit {{ background: {COLORS['crit']}; }}

.wt_live {{
    display: inline-flex; align-items: center; gap: 7px;
    padding: 3px 12px; border-radius: 999px;
    background: rgba(30,120,184,0.12); color: #1E78B8;
    font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
}}
.wt_live .wt_dot {{ width: 7px; height: 7px; }}
.wt_live.on .wt_dot {{ animation: wt_pulse 1.6s ease-out infinite; }}
@keyframes wt_pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(30,120,184,0.5); }}
    70% {{ box-shadow: 0 0 0 7px rgba(30,120,184,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(30,120,184,0); }}
}}
.wt_live.off {{ background: rgba(148,163,184,0.16); color: {COLORS['muted']}; }}

.wt_title_row {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px; margin-bottom: 2px;
}}
.wt_title {{
    font-size: 26px; font-weight: 700; color: {COLORS['ink']};
    letter-spacing: -0.01em; line-height: 1.1;
}}
.wt_tagline {{ font-size: 13px; color: {COLORS['muted']}; margin-top: 2px; }}
.wt_updated {{ font-size: 12px; color: #6B7280; margin-top: 3px; }}

.wt_legend {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }}

.wt_sys .wt_sysrow {{ display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 13px; }}
.wt_sys .wt_meta {{ font-size: 11px; color: #6B7280; margin-top: 4px; }}
.wt_sys .sep {{ border-top: 1px solid rgba(26,35,50,0.08); margin: 10px 0 6px; }}

.wt_logo {{
    width: 44px; height: 44px; border-radius: 11px;
    background: linear-gradient(140deg, #1E78B8, #155A8A);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 22px; font-weight: 800;
    letter-spacing: -0.02em;
}}

@media (prefers-reduced-motion: reduce) {{
    .wt_live.on .wt_dot {{ animation: none; }}
}}

.wt_footer {{
    margin-top: 28px;
    padding-top: 12px;
    border-top: 1px solid rgba(26,35,50,0.08);
    text-align: center;
    font-size: 12px;
    color: #5B6470;
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def chip(text, tone='ok'):
    return f'<span class="wt_chip {tone}"><span class="wt_dot {tone}"></span>{text}</span>'


def status_chip(status):
    tone = {'Online': 'ok', 'Maintenance': 'warn', 'Offline': 'crit'}.get(status, 'ok')
    return chip(status, tone)


def alert_chip(alert):
    tone = {'Normal': 'ok', 'Warning': 'warn', 'Critical': 'crit'}.get(alert, 'ok')
    return chip(alert, tone)


def dot(tone='ok'):
    return f'<span class="wt_dot {tone}"></span>'


def live_badge(live=True):
    cls = 'on' if live else 'off'
    label = 'LIVE' if live else 'STARTING'
    return f'<span class="wt_live {cls}"><span class="wt_dot"></span>{label}</span>'


def delta_line(cur, prev, invert=False, suffix=''):
    """Build '▲ 3' style delta text + tone. Returns (html, is_flat)."""
    if prev is None:
        return '', True
    diff = cur - prev
    if diff == 0:
        return f'<span style="color:{COLORS["muted"]}">— no change</span>', True
    arrow = '▲' if diff > 0 else '▼'
    good = (diff > 0) if not invert else (diff < 0)
    tone = COLORS['ok'] if good else COLORS['crit']
    return f'<span style="color:{tone}">{arrow} {abs(diff)}{suffix}</span>', False


def kpi_card(label, value, sub_html='', value_color=None, unit=None):
    """Render one KPI card. value may be a string; value_color overrides default ink."""
    vcolor = value_color or COLORS['ink']
    sub = f'<div class="d">{sub_html}</div>' if sub_html else ''
    return (
        f'<div class="wt_card">'
        f'<div class="k">{label}</div>'
        f'<div class="v" style="color:{vcolor}">{value}</div>'
        f'{sub}'
        f'</div>'
    )


def render_header(title, tagline, live=True, updated=True):
    st.markdown(
        f'<div class="wt_title_row">'
        f'<div class="wt_title">{title}</div>'
        f'{live_badge(live)}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="wt_tagline">{tagline}</div>', unsafe_allow_html=True)
    if updated:
        st.markdown(
            f'<div class="wt_updated">Last updated: {datetime.now().strftime("%H:%M:%S")}</div>',
            unsafe_allow_html=True,
        )


def render_legend(items):
    """items: list of (text, tone)."""
    row = ''.join(f'<span class="wt_chip {t}"><span class="wt_dot {t}"></span>{txt}</span>'
                  for txt, t in items)
    st.markdown(f'<div class="wt_legend">{row}</div>', unsafe_allow_html=True)


def style_fig(fig, height=None):
    """Apply the shared sky-light layout to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT, color=COLORS['muted'], size=12),
        title=dict(font=dict(color=COLORS['ink'], size=15), x=0.01, xanchor='left'),
        margin=dict(t=44, b=12, l=12, r=12),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=COLORS['muted'])),
        hoverlabel=dict(bgcolor='#FFFFFF', font=dict(color=COLORS['ink'])),
    )
    fig.update_xaxes(gridcolor=COLORS['grid'])
    fig.update_yaxes(gridcolor=COLORS['grid'])
    if height:
        fig.update_layout(height=height)
    return fig