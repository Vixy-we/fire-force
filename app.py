"""
app.py

Main Streamlit entry point.
"""
import streamlit as st
import psychrolib
import psychro_calc
import chart
import ui_components
from process_config import PROCESS_CONFIG

# Basic Setup
st.set_page_config(
    layout="wide",
    page_title="Psychrometric Visualizer",
    page_icon="🌡️",
    initial_sidebar_state="expanded",
)

# Theme Setup
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

with st.sidebar:
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)

theme_colors = ui_components.get_theme_colors(st.session_state.dark_mode)

tc_text_sec = theme_colors["text_secondary"]
tc_text_pri = theme_colors["text_primary"]
tc_border = theme_colors["border"]
tc_accent = theme_colors["accent"]

# Load layout overrides
ui_components.inject_css(theme_colors)
ui_components.render_header(theme_colors)


# ── Helper to build styled label HTML without backslash issues ──
def _section_label(text, color):
    return (
        "<div style='color: " + color + "; font-size: 11px; "
        "font-family: Inter, sans-serif; font-weight: 500; "
        "letter-spacing: 1px; text-transform: uppercase;'>"
        + text + "</div>"
    )


def _hr(color):
    return "<hr style='border: none; height: 1px; background-color: " + color + "; margin: 15px 0px;'>"


def _value_display(value_str, color):
    return (
        "<div style='font-family: JetBrains Mono, monospace; color: "
        + color + "; font-size: 18px; font-weight: bold;'>"
        + value_str + "</div>"
    )


# Determine active process
with st.sidebar:
    st.markdown(_hr(tc_border), unsafe_allow_html=True)
    st.markdown(_section_label("PROCESS TYPE", tc_text_sec), unsafe_allow_html=True)

    process_type = st.selectbox(
        "Process Type", list(PROCESS_CONFIG.keys()), label_visibility="collapsed"
    )
    process_color = PROCESS_CONFIG[process_type]["color"]
    description = PROCESS_CONFIG[process_type]["description"]

    # Inline dot
    dot_html = (
        "<div style='display: flex; align-items: center; gap: 8px;'>"
        "<div style='width: 8px; height: 8px; border-radius: 50%; "
        "background-color: " + process_color + ";'></div>"
        "<span style='color: " + tc_text_pri + "; font-family: Inter, sans-serif; "
        "font-size: 13px; font-weight: 500;'>" + process_type + "</span>"
        "</div>"
    )
    st.markdown(dot_html, unsafe_allow_html=True)

    st.markdown(_hr(tc_border), unsafe_allow_html=True)

    # Inlet Input section
    st.markdown(_section_label("INLET AIR STATE", tc_text_sec), unsafe_allow_html=True)
    in_dbt = st.slider("Dry Bulb Temperature (°C)", 0.0, 50.0, 35.0, 0.5, key="in_dbt")
    st.markdown(_value_display(f"{in_dbt:.1f}", tc_accent), unsafe_allow_html=True)

    in_rh = st.slider("Relative Humidity (%)", 5, 95, 60, 1, key="in_rh")
    st.markdown(_value_display(str(in_rh), tc_accent), unsafe_allow_html=True)

    # Conditionally Required Inputs
    out_dbt = None
    out_rh = None
    target_rh = None
    m_ratio = None

    required_inputs = PROCESS_CONFIG[process_type]["inputs"]

    # Check if we need a second process step section
    if len(required_inputs) > 2:
        st.markdown(_hr(tc_border), unsafe_allow_html=True)
        st.markdown(_section_label("OUTLET AIR STATE", tc_text_sec), unsafe_allow_html=True)

        if "outlet_DBT" in required_inputs:
            default_out_dbt = 25.0 if process_type != "Sensible Heating" else 45.0
            out_dbt = st.slider("Outlet Dry Bulb Temperature (°C)", 0.0, 50.0, default_out_dbt, 0.5, key="out_dbt")
            st.markdown(_value_display(f"{out_dbt:.1f}", process_color), unsafe_allow_html=True)

        if "outlet_RH" in required_inputs:
            out_rh = st.slider("Outlet Relative Humidity (%)", 5, 95, 50, 1, key="out_rh")
            st.markdown(_value_display(str(out_rh), process_color), unsafe_allow_html=True)

        if "target_RH" in required_inputs:
            target_rh = st.slider("Target Relative Humidity (%)", 5, 95, 90, 1, key="target_rh")
            st.markdown(_value_display(str(target_rh), process_color), unsafe_allow_html=True)

        if "DBT2" in required_inputs:
            out_dbt = st.slider("Stream 2 Dry Bulb Temp (°C)", 0.0, 50.0, 20.0, 0.5, key="mix_dbt")
            st.markdown(_value_display(f"{out_dbt:.1f}", process_color), unsafe_allow_html=True)
            out_rh = st.slider("Stream 2 Relative Humidity (%)", 5, 95, 40, 1, key="mix_rh")
            st.markdown(_value_display(str(out_rh), process_color), unsafe_allow_html=True)
            m_ratio = st.slider("Mass Flow Ratio (Stream 1 / Total)", 0.1, 0.9, 0.5, 0.05)
            st.markdown(_value_display(f"{m_ratio:.2f}", process_color), unsafe_allow_html=True)

    st.markdown(_hr(tc_border), unsafe_allow_html=True)
    st.markdown(_section_label("CHART OPTIONS", tc_text_sec), unsafe_allow_html=True)

    chart_config = {
        "Show RH Lines": st.checkbox("Show RH Lines", value=True),
        "Show Enthalpy Lines": st.checkbox("Show Enthalpy Lines", value=True),
        "Show WBT Lines": st.checkbox("Show WBT Lines", value=False),
        "Show Comfort Zone": st.checkbox("Show Comfort Zone", value=True),
        "Show Property Tooltips": st.checkbox("Show Property Tooltips", value=True),
    }

    st.markdown("<br>", unsafe_allow_html=True)
    calc_button = st.button("CALCULATE PROCESS")
    st.markdown(
        "<div style='color: " + tc_text_sec + "; font-size: 10px; "
        "margin-top: 8px; text-align: center;'>Powered by PsychroLib · ASHRAE SI</div>",
        unsafe_allow_html=True,
    )

# Main container for display
st.markdown("<div style='padding: 24px 32px;'>", unsafe_allow_html=True)

# Generate baseline chart
fig = chart.build_psychro_chart(chart_config, theme_colors)

in_state = None
out_state = None
process_results = None
is_valid_flow = False

# Evaluate
if calc_button:
    if process_type == "Adiabatic Mixing of Two Streams":
        val_in, msg_in = psychro_calc.validate_state(in_dbt, in_rh)
        val_out, msg_out = psychro_calc.validate_state(out_dbt, out_rh)
        if not val_in:
            st.error(f"Invalid Stream 1 state: {msg_in}")
        elif not val_out:
            st.error(f"Invalid Stream 2 state: {msg_out}")
        else:
            is_valid_flow = True
    else:
        val_in, msg_in = psychro_calc.validate_state(in_dbt, in_rh)
        out_eval_dbt = out_dbt if out_dbt is not None else in_dbt
        out_eval_rh = out_rh if out_rh is not None else in_rh
        target_eval_rh = target_rh if target_rh is not None else 90

        if process_type in ["Sensible Heating", "Sensible Cooling"]:
            dummy_rh = in_rh
            val_out, msg_out = psychro_calc.validate_state(out_eval_dbt, dummy_rh, in_dbt, in_rh, process_type)
        elif process_type == "Evaporative Cooling":
            val_out, msg_out = psychro_calc.validate_state(in_dbt, in_rh, in_dbt, in_rh, process_type, target_eval_rh)
        else:
            val_out, msg_out = psychro_calc.validate_state(out_eval_dbt, out_eval_rh, in_dbt, in_rh, process_type)

        if not val_in:
            st.error(f"Invalid Inlet state: {msg_in}")
        elif not val_out:
            st.error(f"Invalid State: {msg_out} Adjust inputs.")
        else:
            is_valid_flow = True

    # Compute values and append state points if flow is physically valid
    if is_valid_flow:
        st.toast("Process calculated successfully", icon="✅")
        in_state = psychro_calc.calculate_state(in_dbt, in_rh)

        if process_type in ["Sensible Heating", "Sensible Cooling"]:
            # Humidity ratio stays constant; compute the resulting RH at new DBT
            W_in = in_state["W"]
            actual_rh_out = psychrolib.GetRelHumFromHumRatio(out_dbt, W_in, psychro_calc.P_ATM) * 100
            # Clamp to valid range — can exceed 100% if W_in > saturation at out_dbt
            actual_rh_out = max(0.0, min(100.0, actual_rh_out))
            out_state = psychro_calc.calculate_state(out_dbt, actual_rh_out)
        elif process_type == "Evaporative Cooling":
            out_state = psychro_calc.calculate_evaporative_cooling_state(in_state, target_rh)
        elif process_type == "Adiabatic Mixing of Two Streams":
            stream2 = psychro_calc.calculate_state(out_dbt, out_rh)
            out_state = psychro_calc.calculate_mixed_state(in_state, stream2, m_ratio)
        else:
            out_state = psychro_calc.calculate_state(out_dbt, out_rh)

        process_results = psychro_calc.calculate_process(in_state, out_state, process_type, m_ratio)
        fig = chart.add_state_points(fig, in_state, out_state, process_type, process_color, theme_colors)

plotly_config = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "filename": "psychrometric_chart", "scale": 2},
}
st.plotly_chart(fig, width="stretch", config=plotly_config)

# Layout bottom panels
col1, col2, col3 = st.columns([1, 1.2, 1])

with col1:
    if in_state:
        ui_components.render_state_panel(in_state, "INLET STATE", tc_accent, theme_colors)

with col2:
    if process_results:
        ui_components.render_process_results(process_results, process_type, process_color, description, theme_colors)
    elif calc_button and not is_valid_flow:
        pass
    else:
        st.markdown(
            "<div style='color: " + tc_text_sec + "; font-style: italic; "
            "text-align: center; margin-top: 50px;'>"
            "Configure condition boundaries and press Calculate</div>",
            unsafe_allow_html=True,
        )

with col3:
    if out_state:
        ui_components.render_state_panel(out_state, "OUTLET STATE", process_color, theme_colors, delta_state=in_state, is_outlet=True)

st.markdown("</div>", unsafe_allow_html=True)
