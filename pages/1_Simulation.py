"""
AHU Journey Simulation — Psychrometric Process Visualizer
Simulates air moving through each stage of an Air Handling Unit,
plotting the evolving state point live on the psychrometric chart.

Adapted to work with the existing psychro_visualizer module API.
"""

import time
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import psychrolib

# Import from existing project modules
from psychro_calc import calculate_state, validate_state, P_ATM
from chart import build_psychro_chart
from ui_components import get_theme_colors, inject_css, render_header, render_theme_toggle

# ─── PsychroLib init ────────────────────────────────────────────────────────
psychrolib.SetUnitSystem(psychrolib.SI)

# ─── Constants ──────────────────────────────────────────────────────────────
C_PA = 1.006    # Specific heat of dry air, kJ/kg·K
H_FG = 2501.0   # Latent heat of vaporization at 0°C, kJ/kg
C_PV = 1.86     # Specific heat of water vapour, kJ/kg·K

# AHU stage definitions — each stage has a name, color, and description
AHU_STAGES = [
    {
        "id": "outdoor",
        "label": "① Outdoor Air",
        "color": "#FF6B35",
        "description": "Raw outdoor air enters the AHU. Hot and humid in summer.",
        "icon": "🌤️"
    },
    {
        "id": "mixing",
        "label": "② Mixed Air",
        "color": "#FFD700",
        "description": "Outdoor air mixes with return air from the conditioned space. Reduces cooling load.",
        "icon": "🔀"
    },
    {
        "id": "cooling_coil",
        "label": "③ After Cooling Coil",
        "color": "#7B2FFF",
        "description": "Mixed air passes over the chilled water coil. Temperature drops, moisture condenses.",
        "icon": "❄️"
    },
    {
        "id": "fan",
        "label": "④ After Supply Fan",
        "color": "#00C9FF",
        "description": "Fan work adds small heat gain to the air stream before it enters the duct.",
        "icon": "💨"
    },
    {
        "id": "supply",
        "label": "⑤ Supply Air",
        "color": "#00E676",
        "description": "Conditioned air delivered to the space. Cool and dehumidified.",
        "icon": "🏢"
    },
]

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AHU Simulation — Psychrometric Visualizer",
    page_icon="🏭",
    layout="wide"
)

# ─── Theme ──────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ─── Theme toggle at top of sidebar ─────────────────────────────────────────
with st.sidebar:
    st.session_state.dark_mode = render_theme_toggle()

colors = get_theme_colors(st.session_state.get("dark_mode", True))
inject_css(colors)
render_header(colors)

# ─── Extra simulation-specific CSS ──────────────────────────────────────────
st.markdown(f"""
<style>
.stage-card {{
    background: {colors['card_bg']};
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid {colors['border']};
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px {colors['shadow']};
}}
.stage-card.active {{
    border-left: 4px solid {colors['accent']};
    background: {colors['bg']};
}}
.stage-card.complete {{
    border-left: 4px solid #00E676;
    opacity: 0.75;
}}
.stage-label {{
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: {colors['text_primary']};
    margin-bottom: 4px;
}}
.stage-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: {colors['text_secondary']};
    line-height: 1.5;
}}
.stage-values {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: {colors['accent']};
    margin-top: 6px;
}}
.sim-badge {{
    display: inline-block;
    background: {colors['card_bg']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: {colors['text_secondary']};
    margin-right: 6px;
}}
.energy-bar-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: {colors['text_secondary']};
}}
.schematic-container {{
    background: {colors['card_bg']};
    border-radius: 10px;
    padding: 16px;
    border: 1px solid {colors['border']};
    margin-bottom: 16px;
    box-shadow: 0 4px 6px {colors['shadow']};
}}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PSYCHROMETRIC CALCULATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def compute_ahu_stages(outdoor_DBT, outdoor_RH_dec, return_DBT, return_RH_dec,
                        mixing_ratio, coil_DBT, coil_RH_pct, fan_heat_gain):
    """
    Compute psychrometric state at each AHU stage.

    Our calculate_state returns keys: DBT, WBT, RH, W, W_gkg, h, v
    This function adapts them for the simulation.

    Args:
        outdoor_DBT: Outdoor dry bulb temperature, °C
        outdoor_RH_dec: Outdoor relative humidity, 0-1 (decimal)
        return_DBT: Return air dry bulb temperature, °C
        return_RH_dec: Return air relative humidity, 0-1 (decimal)
        mixing_ratio: Fraction of outdoor air in mixed stream, 0-1
        coil_DBT: Cooling coil outlet dry bulb temperature, °C
        coil_RH_pct: Cooling coil outlet relative humidity, % (5-95)
        fan_heat_gain: Heat added by fan, kJ/kg dry air

    Returns:
        dict: State dict for each AHU stage keyed by stage id
    """
    stages = {}

    # Stage 1 — Outdoor air state
    stages["outdoor"] = calculate_state(outdoor_DBT, outdoor_RH_dec * 100)

    # Stage 2 — Mixed air state (lever rule on humidity ratio and enthalpy)
    outdoor_W = stages["outdoor"]["W"]
    outdoor_h = stages["outdoor"]["h"]

    return_state = calculate_state(return_DBT, return_RH_dec * 100)
    return_W = return_state["W"]
    return_h = return_state["h"]

    # Lever rule: mixed = outdoor * ratio + return * (1 - ratio)
    mixed_W = mixing_ratio * outdoor_W + (1 - mixing_ratio) * return_W
    mixed_h = mixing_ratio * outdoor_h + (1 - mixing_ratio) * return_h

    # Recover DBT from mixed enthalpy and humidity ratio
    # h = C_PA * T + W * (H_FG + C_PV * T)  →  solve for T
    mixed_DBT = (mixed_h - H_FG * mixed_W) / (C_PA + C_PV * mixed_W)
    mixed_RH = psychrolib.GetRelHumFromHumRatio(mixed_DBT, mixed_W, P_ATM)
    mixed_RH_pct = max(0.0, min(100.0, mixed_RH * 100))
    stages["mixing"] = calculate_state(mixed_DBT, mixed_RH_pct)
    # Store return state for schematic reference
    stages["return"] = return_state

    # Stage 3 — Cooling coil outlet (cooling and dehumidification)
    stages["cooling_coil"] = calculate_state(coil_DBT, coil_RH_pct)

    # Stage 4 — After supply fan
    # Fan work adds sensible heat only — humidity ratio unchanged
    coil_W = stages["cooling_coil"]["W"]
    coil_h = stages["cooling_coil"]["h"]
    fan_h = coil_h + fan_heat_gain  # Enthalpy rises by fan heat gain
    fan_DBT = (fan_h - H_FG * coil_W) / (C_PA + C_PV * coil_W)
    fan_RH = psychrolib.GetRelHumFromHumRatio(fan_DBT, coil_W, P_ATM)
    fan_RH_pct = max(0.0, min(95.0, fan_RH * 100))
    stages["fan"] = calculate_state(fan_DBT, fan_RH_pct)

    # Stage 5 — Supply air (same as post-fan for basic AHU)
    stages["supply"] = stages["fan"]

    return stages


def interpolate_path(state_a, state_b, n_steps=40):
    """
    Generate intermediate psychrometric states between two points.
    """
    dbt_path = np.linspace(state_a["DBT"], state_b["DBT"], n_steps)
    w_path = np.linspace(state_a["W"], state_b["W"], n_steps)
    return list(zip(dbt_path, w_path))


def build_energy_breakdown(stages):
    """
    Compute energy quantities for each AHU stage transition.
    """
    mixing_cooling = stages["outdoor"]["h"] - stages["mixing"]["h"]
    coil_total = stages["mixing"]["h"] - stages["cooling_coil"]["h"]
    coil_sensible = C_PA * (
        stages["mixing"]["DBT"] - stages["cooling_coil"]["DBT"]
    )
    coil_latent = coil_total - coil_sensible
    moisture_removed = (
        stages["mixing"]["W"] - stages["cooling_coil"]["W"]
    ) * 1000  # Convert to g/kg
    fan_gain = stages["fan"]["h"] - stages["cooling_coil"]["h"]
    total_load = stages["outdoor"]["h"] - stages["supply"]["h"]

    return {
        "mixing_benefit": max(0, mixing_cooling),
        "coil_total": max(0, coil_total),
        "coil_sensible": max(0, coil_sensible),
        "coil_latent": max(0, coil_latent),
        "moisture_removed_g": max(0, moisture_removed),
        "fan_gain": max(0, fan_gain),
        "total_cooling_load": max(0, total_load),
    }


# ════════════════════════════════════════════════════════════════════════════
# CHART BUILDING FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def build_simulation_chart(stages, current_stage_idx, clrs, show_trail=True):
    """
    Build the psychrometric chart for the simulation with all AHU stage
    points and the animated trail up to current_stage_idx.
    """
    # Use the same config key names as chart.py expects
    chart_config = {
        "Show RH Lines": True,
        "Show Enthalpy Lines": True,
        "Show WBT Lines": False,
        "Show Comfort Zone": True,
    }
    fig = build_psychro_chart(chart_config, clrs)

    stage_ids = [s["id"] for s in AHU_STAGES]

    # Draw trail lines between completed stages
    if show_trail and current_stage_idx > 0:
        for i in range(current_stage_idx):
            id_a = stage_ids[i]
            id_b = stage_ids[i + 1]
            if id_a not in stages or id_b not in stages:
                continue
            state_a = stages[id_a]
            state_b = stages[id_b]
            stage_color = AHU_STAGES[i + 1]["color"]

            fig.add_trace(go.Scatter(
                x=[state_a["DBT"], state_b["DBT"]],
                y=[state_a["W"], state_b["W"]],
                mode="lines",
                line=dict(color=stage_color, width=2.5, dash="solid"),
                showlegend=False,
                hoverinfo="skip",
            ))

            # Midpoint arrow annotation
            mid_x = (state_a["DBT"] + state_b["DBT"]) / 2
            mid_y = (state_a["W"] + state_b["W"]) / 2
            fig.add_annotation(
                x=state_b["DBT"],
                y=state_b["W"],
                ax=mid_x,
                ay=mid_y,
                axref="x", ayref="y",
                arrowhead=2,
                arrowsize=1.5,
                arrowcolor=stage_color,
                arrowwidth=2,
                showarrow=True,
            )

    # Plot all stage points up to current
    for i in range(current_stage_idx + 1):
        stage_def = AHU_STAGES[i]
        sid = stage_def["id"]
        if sid not in stages:
            continue
        state = stages[sid]
        is_current = (i == current_stage_idx)

        # Build hover text
        hover = (
            f"<b>{stage_def['label']}</b><br>"
            f"DBT: {state['DBT']:.1f} °C<br>"
            f"WBT: {state['WBT']:.1f} °C<br>"
            f"RH: {state['RH']:.1f} %<br>"
            f"ω: {state['W']*1000:.2f} g/kg<br>"
            f"h: {state['h']:.2f} kJ/kg"
        )

        fig.add_trace(go.Scatter(
            x=[state["DBT"]],
            y=[state["W"]],
            mode="markers+text",
            marker=dict(
                color=stage_def["color"],
                size=16 if is_current else 11,
                symbol="circle",
                line=dict(
                    color="#FFFFFF" if is_current else "#0F1117",
                    width=2.5 if is_current else 1.5
                )
            ),
            text=[stage_def["icon"]],
            textposition="top center",
            textfont=dict(size=14),
            name=stage_def["label"],
            hovertemplate=hover + "<extra></extra>",
            showlegend=True,
        ))

        # Pulse ring on current active point
        if is_current:
            fig.add_trace(go.Scatter(
                x=[state["DBT"]],
                y=[state["W"]],
                mode="markers",
                marker=dict(
                    color="rgba(0,201,255,0.0)",
                    size=28,
                    symbol="circle",
                    line=dict(color=stage_def["color"], width=1.5)
                ),
                showlegend=False,
                hoverinfo="skip",
            ))

    # Legend styling
    fig.update_layout(
        legend=dict(
            font=dict(color=clrs.get("text_secondary", "#8B95A5"), size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#2A3140",
            borderwidth=1,
            x=1.01,
            y=0.99,
            xanchor="left",
        ),
        height=500,
    )

    return fig


def build_schematic_svg(current_stage_idx, clrs):
    """
    Build an SVG schematic of the AHU showing which component is
    currently active, highlighted in the stage's accent color.
    """
    stage_ids = [s["id"] for s in AHU_STAGES]
    current_id = stage_ids[current_stage_idx] if current_stage_idx < len(stage_ids) else None

    def comp_color(sid):
        for i, s in enumerate(AHU_STAGES):
            if s["id"] == sid:
                if sid == current_id:
                    return s["color"]
                elif i < current_stage_idx:
                    return "#00E676"
                else:
                    return "#2A3140"
        return "#2A3140"

    def text_color(sid):
        if sid == current_id:
            return "#0F1117"
        return "#8B95A5"

    outdoor_c = comp_color("outdoor")
    mixing_c = comp_color("mixing")
    coil_c = comp_color("cooling_coil")
    fan_c = comp_color("fan")
    supply_c = comp_color("supply")

    svg = f"""
    <div style="background:{clrs['card_bg']}; border-radius:10px; padding:16px;
                border:1px solid {clrs['border']}; margin-bottom:16px;">
      <div style="font-family:'Inter',sans-serif; font-size:11px;
                  color:{clrs['text_secondary']}; letter-spacing:1px; margin-bottom:12px;">
        AHU SCHEMATIC — LIVE STAGE TRACKING
      </div>
      <svg viewBox="0 0 700 120" xmlns="http://www.w3.org/2000/svg"
           style="width:100%; height:auto;">

        <!-- Outdoor air arrow in -->
        <line x1="10" y1="60" x2="80" y2="60"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>
        <text x="10" y="50" fill="#8B95A5" font-size="9"
              font-family="JetBrains Mono">OUTDOOR</text>

        <!-- Outdoor box -->
        <rect x="80" y="35" width="80" height="50" rx="6"
              fill="{outdoor_c}" opacity="0.9"/>
        <text x="120" y="57" fill="{text_color('outdoor')}"
              font-size="9" font-weight="600" font-family="Inter"
              text-anchor="middle">OUTDOOR</text>
        <text x="120" y="72" fill="{text_color('outdoor')}"
              font-size="9" font-family="Inter" text-anchor="middle">
          AIR
        </text>

        <!-- Arrow to mixing box -->
        <line x1="160" y1="60" x2="210" y2="60"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>

        <!-- Return air arrow from top -->
        <line x1="235" y1="10" x2="235" y2="35"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>
        <text x="215" y="10" fill="#8B95A5" font-size="9"
              font-family="JetBrains Mono">RETURN</text>

        <!-- Mixing box -->
        <rect x="210" y="35" width="80" height="50" rx="6"
              fill="{mixing_c}" opacity="0.9"/>
        <text x="250" y="57" fill="{text_color('mixing')}"
              font-size="9" font-weight="600" font-family="Inter"
              text-anchor="middle">MIXING</text>
        <text x="250" y="72" fill="{text_color('mixing')}"
              font-size="9" font-family="Inter" text-anchor="middle">
          BOX
        </text>

        <!-- Arrow to cooling coil -->
        <line x1="290" y1="60" x2="340" y2="60"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>

        <!-- Cooling coil box -->
        <rect x="340" y="35" width="80" height="50" rx="6"
              fill="{coil_c}" opacity="0.9"/>
        <text x="380" y="54" fill="{text_color('cooling_coil')}"
              font-size="9" font-weight="600" font-family="Inter"
              text-anchor="middle">COOLING</text>
        <text x="380" y="67" fill="{text_color('cooling_coil')}"
              font-size="9" font-family="Inter" text-anchor="middle">
          COIL
        </text>
        <text x="380" y="80" fill="{text_color('cooling_coil')}"
              font-size="8" font-family="JetBrains Mono"
              text-anchor="middle">❄️</text>

        <!-- Arrow to fan -->
        <line x1="420" y1="60" x2="470" y2="60"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>

        <!-- Fan box -->
        <rect x="470" y="35" width="80" height="50" rx="6"
              fill="{fan_c}" opacity="0.9"/>
        <text x="510" y="57" fill="{text_color('fan')}"
              font-size="9" font-weight="600" font-family="Inter"
              text-anchor="middle">SUPPLY</text>
        <text x="510" y="72" fill="{text_color('fan')}"
              font-size="9" font-family="Inter" text-anchor="middle">
          FAN 💨
        </text>

        <!-- Arrow to supply -->
        <line x1="550" y1="60" x2="600" y2="60"
              stroke="#8B95A5" stroke-width="2" marker-end="url(#arr)"/>

        <!-- Supply box -->
        <rect x="600" y="35" width="80" height="50" rx="6"
              fill="{supply_c}" opacity="0.9"/>
        <text x="640" y="57" fill="{text_color('supply')}"
              font-size="9" font-weight="600" font-family="Inter"
              text-anchor="middle">SUPPLY</text>
        <text x="640" y="72" fill="{text_color('supply')}"
              font-size="9" font-family="Inter" text-anchor="middle">
          AIR 🏢
        </text>

        <!-- Arrow marker definition -->
        <defs>
          <marker id="arr" markerWidth="6" markerHeight="6"
                  refX="3" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#8B95A5"/>
          </marker>
        </defs>
      </svg>
    </div>
    """
    return svg


# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ════════════════════════════════════════════════════════════════════════════

if "sim_stages" not in st.session_state:
    st.session_state.sim_stages = None
if "sim_current_idx" not in st.session_state:
    st.session_state.sim_current_idx = 0
if "sim_running" not in st.session_state:
    st.session_state.sim_running = False
if "sim_energy" not in st.session_state:
    st.session_state.sim_energy = None
if "sim_calculated" not in st.session_state:
    st.session_state.sim_calculated = False


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — SIMULATION INPUTS
# ════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:{colors['text_secondary']}; letter-spacing:1px; margin-bottom:4px;'>
        AHU JOURNEY SIMULATION
    </div>
    <div style='font-family:Inter,sans-serif; font-size:10px;
                color:{colors['border']}; margin-bottom:16px;'>
        ────────────────────────
    </div>
    """, unsafe_allow_html=True)

    # ── Outdoor air ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:{colors['text_secondary']}; letter-spacing:1px; margin-bottom:8px;'>
        🌤️ OUTDOOR AIR STATE
    </div>
    """, unsafe_allow_html=True)

    outdoor_DBT = st.slider(
        "Outdoor DBT (°C)", 25.0, 48.0, 38.0, 0.5,
        key="outdoor_dbt"
    )
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace; "
        f"font-size:18px; color:#FF6B35; font-weight:700; "
        f"margin-bottom:8px;'>{outdoor_DBT:.1f} °C</div>",
        unsafe_allow_html=True
    )

    outdoor_RH = st.slider(
        "Outdoor RH (%)", 20, 90, 55, 1,
        key="outdoor_rh"
    ) / 100
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace; "
        f"font-size:18px; color:#FF6B35; font-weight:700; "
        f"margin-bottom:16px;'>{outdoor_RH*100:.0f} %</div>",
        unsafe_allow_html=True
    )

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Return air ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:{colors['text_secondary']}; letter-spacing:1px; margin-bottom:8px;'>
        🔁 RETURN AIR STATE
    </div>
    """, unsafe_allow_html=True)

    return_DBT = st.slider(
        "Return DBT (°C)", 20.0, 30.0, 24.0, 0.5,
        key="return_dbt"
    )
    return_RH = st.slider(
        "Return RH (%)", 30, 70, 50, 1,
        key="return_rh"
    ) / 100

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Mixing ratio ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:{colors['text_secondary']}; letter-spacing:1px; margin-bottom:8px;'>
        🔀 MIXING BOX
    </div>
    """, unsafe_allow_html=True)

    mixing_ratio = st.slider(
        "Fresh Air Fraction", 0.10, 0.90, 0.30, 0.05,
        key="mixing_ratio",
        help="Fraction of outdoor air in the mixed stream. 0.3 = 30% fresh air."
    )
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace; "
        f"font-size:12px; color:#FFD700; margin-bottom:16px;'>"
        f"{mixing_ratio*100:.0f}% outdoor · "
        f"{(1-mixing_ratio)*100:.0f}% return</div>",
        unsafe_allow_html=True
    )

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Cooling coil ────────────────────────────────────────────────────────
    st.markdown("""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:#8B95A5; letter-spacing:1px; margin-bottom:8px;'>
        ❄️ COOLING COIL OUTLET
    </div>
    """, unsafe_allow_html=True)

    coil_DBT = st.slider(
        "Coil Outlet DBT (°C)", 10.0, 22.0, 13.0, 0.5,
        key="coil_dbt"
    )
    coil_RH = st.slider(
        "Coil Outlet RH (%)", 80, 95, 90, 1,
        key="coil_rh"
    )

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Fan heat gain ───────────────────────────────────────────────────────
    st.markdown("""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:#8B95A5; letter-spacing:1px; margin-bottom:8px;'>
        💨 FAN HEAT GAIN
    </div>
    """, unsafe_allow_html=True)

    fan_heat = st.slider(
        "Fan Heat Gain (kJ/kg)", 0.5, 3.0, 1.0, 0.1,
        key="fan_heat",
        help="Mechanical energy from fan motor added as heat to air stream."
    )

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Animation speed ─────────────────────────────────────────────────────
    anim_speed = st.select_slider(
        "Animation Speed",
        options=["Slow", "Medium", "Fast"],
        value="Medium",
        key="anim_speed"
    )
    speed_map = {"Slow": 1.2, "Medium": 0.6, "Fast": 0.25}
    step_delay = speed_map[anim_speed]

    st.markdown("<hr style='border-color:#2A3140;'>", unsafe_allow_html=True)

    # ── Control buttons ──────────────────────────────────────────────────────
    col_run, col_reset = st.columns(2)
    with col_run:
        run_btn = st.button(
            "▶ RUN",
            use_container_width=True,
            key="run_btn"
        )
    with col_reset:
        reset_btn = st.button(
            "↺ RESET",
            use_container_width=True,
            key="reset_btn"
        )

    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace; "
        f"font-size:10px; color:{colors['text_secondary']}; text-align:center; "
        f"margin-top:8px;'>AHU Journey · PsychroLib SI</div>",
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT AREA
# ════════════════════════════════════════════════════════════════════════════

# ── Page title ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-bottom:8px;'>
  <span style='font-family:Inter,sans-serif; font-weight:700;
               font-size:22px; color:{colors["text_primary"]}; letter-spacing:1px;'>
    AHU JOURNEY
  </span>
  <span style='font-family:Inter,sans-serif; font-size:13px;
               color:{colors["text_secondary"]}; margin-left:12px;'>
    Air Handling Unit — Psychrometric State Evolution
  </span>
</div>
<div style='font-family:Inter,sans-serif; font-size:12px;
            color:{colors["text_secondary"]}; margin-bottom:20px; line-height:1.6;'>
  Watch outdoor air transform as it moves through each AHU stage.
  Each point on the chart represents the air state at that equipment stage.
  The trail shows the thermodynamic path taken.
</div>
""", unsafe_allow_html=True)

# ── Handle reset ─────────────────────────────────────────────────────────────
if reset_btn:
    st.session_state.sim_stages = None
    st.session_state.sim_current_idx = 0
    st.session_state.sim_running = False
    st.session_state.sim_energy = None
    st.session_state.sim_calculated = False
    st.rerun()

# ── Handle run ───────────────────────────────────────────────────────────────
if run_btn:
    # Validate inputs
    valid_outdoor, err_outdoor = validate_state(outdoor_DBT, outdoor_RH * 100)
    valid_return, err_return = validate_state(return_DBT, return_RH * 100)
    valid_coil, err_coil = validate_state(coil_DBT, coil_RH)

    if not valid_outdoor:
        st.error(f"Outdoor air state invalid: {err_outdoor}")
    elif not valid_return:
        st.error(f"Return air state invalid: {err_return}")
    elif not valid_coil:
        st.error(f"Cooling coil outlet invalid: {err_coil}")
    elif coil_DBT >= outdoor_DBT:
        st.error("Coil outlet DBT must be less than outdoor DBT.")
    else:
        stages = compute_ahu_stages(
            outdoor_DBT, outdoor_RH,
            return_DBT, return_RH,
            mixing_ratio,
            coil_DBT, coil_RH,
            fan_heat
        )
        st.session_state.sim_stages = stages
        st.session_state.sim_energy = build_energy_breakdown(stages)
        st.session_state.sim_current_idx = 0
        st.session_state.sim_running = True
        st.session_state.sim_calculated = True

# ── Schematic placeholder ─────────────────────────────────────────────────────
schematic_slot = st.empty()

# ── Chart and stage panel ─────────────────────────────────────────────────────
chart_col, stage_col = st.columns([2.2, 1])

with chart_col:
    chart_slot = st.empty()

with stage_col:
    st.markdown("""
    <div style='font-family:Inter,sans-serif; font-size:11px;
                color:#8B95A5; letter-spacing:1px; margin-bottom:12px;'>
        STAGE PROGRESS
    </div>
    """, unsafe_allow_html=True)
    stage_slots = [st.empty() for _ in AHU_STAGES]

# ── Energy breakdown ──────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#2A3140; margin:20px 0;'>",
            unsafe_allow_html=True)
st.markdown("""
<div style='font-family:Inter,sans-serif; font-size:11px;
            color:#8B95A5; letter-spacing:1px; margin-bottom:12px;'>
    ENERGY ANALYSIS
</div>
""", unsafe_allow_html=True)
energy_cols = st.columns(4)
energy_slots = [c.empty() for c in energy_cols]


def render_stage_cards(current_idx):
    """Render stage progress cards with active/complete/pending states."""
    for i, stage_def in enumerate(AHU_STAGES):
        if i < current_idx:
            status_class = "complete"
            icon = "✓"
            icon_color = "#00E676"
        elif i == current_idx:
            status_class = "active"
            icon = "●"
            icon_color = stage_def["color"]
        else:
            status_class = ""
            icon = "○"
            icon_color = colors["border"]

        state = st.session_state.sim_stages.get(stage_def["id"]) \
            if st.session_state.sim_stages else None

        values_html = ""
        if state and i <= current_idx:
            values_html = (
                f"<div class='stage-values'>"
                f"DBT {state['DBT']:.1f}°C · "
                f"RH {state['RH']:.0f}% · "
                f"h {state['h']:.1f} kJ/kg"
                f"</div>"
            )

        border_color = stage_def["color"] if i <= current_idx else colors["border"]
        stage_slots[i].markdown(f"""
        <div class='stage-card {status_class}'
             style='border-left-color:{border_color};'>
          <div class='stage-label'>
            <span style='color:{icon_color}; margin-right:6px;'>{icon}</span>
            {stage_def['label']}
          </div>
          <div class='stage-desc'>{stage_def['description']}</div>
          {values_html}
        </div>
        """, unsafe_allow_html=True)


def render_energy_panels(energy, current_idx):
    """Render energy breakdown metric cards."""
    if not energy or current_idx < 2:
        for slot in energy_slots:
            slot.markdown(
                f"<div style='font-family:JetBrains Mono,monospace; "
                f"font-size:11px; color:{colors['text_secondary']}; padding:12px;'>"
                "\u2014 awaiting simulation \u2014</div>",
                unsafe_allow_html=True
            )
        return

    panels = [
        ("TOTAL COOLING LOAD",
         f"{energy['total_cooling_load']:.2f} kJ/kg",
         "#7B2FFF"),
        ("SENSIBLE COOLING",
         f"{energy['coil_sensible']:.2f} kJ/kg",
         "#00C9FF"),
        ("LATENT COOLING",
         f"{energy['coil_latent']:.2f} kJ/kg",
         "#FF6B35"),
        ("MOISTURE REMOVED",
         f"{energy['moisture_removed_g']:.2f} g/kg",
         "#00E676"),
    ]

    for slot, (label, value, color) in zip(energy_slots, panels):
        slot.markdown(f"""
        <div style='background:{colors["card_bg"]}; border-radius:8px; padding:14px;
                    border-left:3px solid {color}; box-shadow: 0 4px 6px {colors["shadow"]};'>
          <div style='font-family:Inter,sans-serif; font-size:10px;
                      color:{colors["text_secondary"]}; letter-spacing:1px;
                      margin-bottom:6px;'>{label}</div>
          <div style='font-family:JetBrains Mono,monospace; font-size:20px;
                      font-weight:700; color:{color};'>{value}</div>
        </div>
        """, unsafe_allow_html=True)


# ── Initial render (no simulation yet) ───────────────────────────────────────
if not st.session_state.sim_calculated:
    chart_config = {
        "Show RH Lines": True,
        "Show Enthalpy Lines": True,
        "Show WBT Lines": False,
        "Show Comfort Zone": True,
    }
    empty_fig = build_psychro_chart(chart_config, colors)
    empty_fig.update_layout(height=500)

    # Add a prompt annotation to the empty chart
    empty_fig.add_annotation(
        x=35, y=0.022,
        text="Configure inputs and press ▶ RUN to start simulation",
        showarrow=False,
        font=dict(color=colors["text_secondary"], size=12, family="Inter"),
        bgcolor=colors["card_bg"],
        opacity=0.9,
        bordercolor=colors["border"],
        borderwidth=1,
        borderpad=8,
    )

    chart_slot.plotly_chart(
        empty_fig,
        width="stretch",
        config={"displaylogo": False},
        key="sim_chart_empty"
    )

    schematic_slot.html(
        build_schematic_svg(0, colors)
    )

    # Empty stage cards
    for i, stage_def in enumerate(AHU_STAGES):
        stage_slots[i].markdown(f"""
        <div class='stage-card'>
          <div class='stage-label'>
            <span style='color:{colors["border"]}; margin-right:6px;'>○</span>
            {stage_def['label']}
          </div>
          <div class='stage-desc'>{stage_def['description']}</div>
        </div>
        """, unsafe_allow_html=True)

    render_energy_panels(None, 0)


# ── Simulation animation loop ─────────────────────────────────────────────────
if st.session_state.sim_running and st.session_state.sim_stages:
    stages = st.session_state.sim_stages
    energy = st.session_state.sim_energy

    for stage_idx in range(len(AHU_STAGES)):
        st.session_state.sim_current_idx = stage_idx

        # Update schematic
        schematic_slot.html(
            build_schematic_svg(stage_idx, colors)
        )

        # Update stage cards
        render_stage_cards(stage_idx)

        # Update energy panels
        render_energy_panels(energy, stage_idx)

        # Update chart
        fig = build_simulation_chart(stages, stage_idx, colors)
        chart_slot.plotly_chart(
            fig,
            width="stretch",
            config={"displaylogo": False, "displayModeBar": True},
            key=f"sim_chart_stage_{stage_idx}"
        )

        time.sleep(step_delay)

    # Simulation complete
    st.session_state.sim_running = False

    st.success(
        "✓ AHU Journey complete — all 5 stages simulated. "
        "Adjust inputs and press RUN again to re-simulate."
    )

    # Final render stays on screen — no rerun
    schematic_slot.html(
        build_schematic_svg(len(AHU_STAGES) - 1, colors)
    )
    render_stage_cards(len(AHU_STAGES) - 1)
    render_energy_panels(energy, len(AHU_STAGES))

    final_fig = build_simulation_chart(
        stages, len(AHU_STAGES) - 1, colors
    )
    chart_slot.plotly_chart(
        final_fig,
        width="stretch",
        config={"displaylogo": False, "displayModeBar": True},
        key="sim_chart_final"
    )

