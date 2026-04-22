"""
ui_components.py

Renders UI components and contains global CSS injection logic.
"""
import streamlit as st


def render_theme_toggle():
    """Renders the dark mode toggle in the sidebar, always visible."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    
    # Consistent label
    colors = get_theme_colors(st.session_state.dark_mode)
    st.markdown(
        f"<div style='font-family:Inter,sans-serif; font-size:11px; "
        f"color:{colors['text_secondary']}; "
        f"letter-spacing:1px; margin-bottom:4px;'>GLOBAL THEME</div>",
        unsafe_allow_html=True
    )
    
    result = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
    st.session_state.dark_mode = result
    return result


def get_theme_colors(is_dark):
    """Return a color palette dict for the chosen theme mode."""
    if is_dark:
        return {
            "bg": "#0F1117",
            "sidebar_bg": "#161B22",
            "card_bg": "#1E2530",
            "text_primary": "#E8EAF0",
            "text_secondary": "#8B95A5",
            "border": "#2A3140",
            "accent": "#00C9FF",
            "grid": "#1E2530",
            "rh_line": "#2A3140",
            "wbt_line": "#1A2A3A",
            "h_line": "#1E3A2F",
            "shadow": "rgba(0,0,0,0.3)",
        }
    else:
        return {
            "bg": "#F8FAFC",
            "sidebar_bg": "#F1F5F9",
            "card_bg": "#FFFFFF",
            "text_primary": "#0F172A",
            "text_secondary": "#64748B",
            "border": "#E2E8F0",
            "accent": "#0ea5e9",
            "grid": "#E2E8F0",
            "rh_line": "#CBD5E1",
            "wbt_line": "#94A3B8",
            "h_line": "#99F6E4",
            "shadow": "rgba(0,0,0,0.05)",
        }


def inject_css(colors):
    """Injects global CSS to style all elements according to custom theme."""
    bg = colors["bg"]
    sidebar_bg = colors["sidebar_bg"]
    card_bg = colors["card_bg"]
    text_pri = colors["text_primary"]
    text_sec = colors["text_secondary"]
    border = colors["border"]
    accent = colors["accent"]
    shadow = colors["shadow"]

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

    /* ── Layout ────────────────────────────────────────────────────── */
    .block-container {{
        padding-top: 0rem;
        padding-bottom: 2rem;
        padding-left: 0rem;
        padding-right: 0rem;
        max-width: 100%;
    }}
    body, .stApp {{
        background-color: {bg};
        font-family: 'Inter', sans-serif;
    }}

    /* ── Advanced Sidebar Reordering ──────────────────────────────── */
    /* Goal: 1. Toggle, 2. Nav Links, 3. Other Sidebar Content */
    
    [data-testid="stSidebar"] > div:first-child {{
        display: flex !important;
        flex-direction: column !important;
    }}

    /* Make the content container transparent to layout */
    [data-testid="stSidebarContent"] {{
        display: contents !important;
    }}

    /* The first two elements are the "GLOBAL THEME" label and the toggle */
    [data-testid="stSidebarContent"] > div:nth-child(1),
    [data-testid="stSidebarContent"] > div:nth-child(2) {{
        order: 1 !important;
    }}

    /* The Nav links (App/Simulation) go in the middle */
    [data-testid="stSidebarNav"] {{
        order: 2 !important;
        background-color: transparent !important;
    }}

    /* All other widgets (n+3) go to the bottom */
    [data-testid="stSidebarContent"] > div:nth-child(n+3) {{
        order: 3 !important;
    }}

    /* ── Sidebar background & nav link colors ─────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid {border};
    }}
    /* Nav link text */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span {{
        color: {text_pri} !important;
    }}
    /* Sidebar section-label stMarkdown — but DON'T use !important so
       inline-styled value-display divs can keep their accent colors */
    [data-testid="stSidebar"] .stMarkdown p {{
        color: {text_pri};
    }}
    /* Widget labels (slider, checkbox, toggle labels) */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
    .stSelectbox label, .stSlider label,
    .stCheckbox label span, .stToggle label span,
    [data-testid="stWidgetLabel"] p {{
        color: {text_sec} !important;
        font-size: 12px !important;
        font-family: 'Inter', sans-serif;
    }}

    /* ── Header ───────────────────────────────────────────────────── */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* ── Metric cards ─────────────────────────────────────────────── */
    div[data-testid="stMetric"] {{
        background-color: {card_bg};
        border-radius: 8px;
        padding: 12px;
        border-left: 3px solid {accent};
        margin-bottom: 8px;
        box-shadow: 0 4px 6px {shadow};
    }}
    div[data-testid="stMetricLabel"] {{
        color: {text_sec} !important;
        font-size: 12px !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-family: 'Inter', sans-serif;
    }}
    div[data-testid="stMetricValue"] {{
        color: {text_pri} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 18px !important;
        font-weight: 600;
    }}

    /* ── Buttons ──────────────────────────────────────────────────── */
    .stButton > button {{
        background-color: {accent} !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        margin-top: 10px;
    }}

    /* ── Sliders — ALWAYS show value and min/max labels ──────────── */
    /* Override EVERY div inside the slider to force opacity visible.
       Streamlit/BaseWeb uses dynamically generated class names with
       opacity:0 that only become opacity:1 on hover. We kill that. */
    [data-testid="stSlider"] div {{
        opacity: 1 !important;
        visibility: visible !important;
    }}
    /* Color the thumb value (current value above the knob) */
    [data-testid="stThumbValue"] {{
        color: {accent} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }}
    /* Color min/max tick labels — use primary color for maximum readability */
    [data-testid="stTickBar"] div,
    [data-testid="stTickBar"] span,
    [data-testid="stTickBar"] p {{
        color: {text_pri} !important;
        opacity: 1 !important;
        visibility: visible !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }}
    /* Specifically target the min and max labels by their unique testids */
    [data-testid="stTickBarMin"],
    [data-testid="stTickBarMax"] {{
        color: {text_pri} !important;
        opacity: 1 !important;
    }}

    /* ── Dialog / Popup ───────────────────────────────────────────── */
    /* Target every possible Streamlit dialog wrapper */
    div[data-testid="stDialog"],
    div[data-testid="stDialog"] > div,
    div[data-testid="stDialog"] > div > div {{
        background-color: {bg} !important;
    }}
    /* All text inside dialog */
    div[data-testid="stDialog"] *:not(code):not(pre) {{
        color: {text_pri} !important;
    }}
    /* Also target by role */
    div[role="dialog"],
    div[role="dialog"] > div {{
        background-color: {bg} !important;
        color: {text_pri} !important;
    }}
    div[role="dialog"] p,
    div[role="dialog"] h1,
    div[role="dialog"] h2,
    div[role="dialog"] h3,
    div[role="dialog"] li,
    div[role="dialog"] span:not([class*="katex"]) {{
        color: {text_pri} !important;
    }}
    /* KaTeX math should remain visible */
    div[role="dialog"] .katex,
    div[role="dialog"] .katex * {{
        color: {text_pri} !important;
    }}

    /* ── Misc ─────────────────────────────────────────────────────── */
    #MainMenu {{visibility: hidden;}}
    .stAppDeployButton {{display: none;}}
    footer {{visibility: hidden;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


@st.dialog("📚 Rules, Formulas & Guide", width="large")
def show_guide_dialog():
    st.markdown("""
### 🌡️ Inputs & Outputs

**Inputs:**
- **Inlet Air State**: Dry Bulb Temperature (DBT) in °C and Relative Humidity (RH) in % or Humidity Ratio/Wet Bulb depending on input mode.
- **Process Parameters**: Target DBT, Target RH, Sensible Heat Gain, or Fresh Air Fraction (depending on the chosen psychrometric process).
- **Atmospheric Pressure**: Fixed to Sea Level standard pressure ($101325\\text{ Pa}$) in this app.

**Outputs:**
- **Outlet Air State**: Computed DBT, WBT, RH, Humidity Ratio ($W$), Enthalpy ($h$), and Specific Volume ($v$).
- **Process Summary**: Total Cooling/Heating Load (kJ/kg), Sensible/Latent Heat components, and Moisture Added/Removed (g/kg).

---

### 🧮 Core Formulas (ASHRAE Fundamentals)

*All psychrometric property calculations in this application use PsychroLib, a scientifically validated library implementing ASHRAE Handbook of Fundamentals (2017) equations. The formulas shown below are the governing relations these calculations are based on.*

**1. Saturation Vapour Pressure ($P_{ws}$)**
Using the Magnus-Tetens empirical approximation for water vapor over liquid water:
$$ P_{ws} = 610.78 \\times \\exp\\left(\\frac{17.27 \\times T}{T + 237.3}\\right) $$
*(Where T is DBT in °C, $P_{ws}$ is in Pa)*

**2. Vapour Pressure ($P_w$) from Relative Humidity**
$$ P_w = \\frac{\\text{RH}}{100} \\times P_{ws} $$

**3. Humidity Ratio ($W$)**
Using the ideal gas ratio of molecular weights for water vapour and dry air (0.621945):
$$ W = 0.622 \\times \\frac{P_w}{P_{atm} - P_w} $$
*(Result in kg water / kg dry air)*

**4. Specific Enthalpy ($h$)**
Combining sensible heat of air and latent heat of vaporisation:
$$ h = 1.006 \\times T + W \\times (2501 + 1.86 \\times T) $$
*(Result in kJ/kg of dry air)*

**5. Specific Volume ($v$)**
$$ v = \\frac{R_{da} \\times (T + 273.15)}{P_{atm} - P_w} $$
*(Where $R_{da} = 287.042$ J/(kg·K))*

**6. Wet Bulb Temperature ($T_{wb}$)**
Solved iteratively from the psychrometric wet bulb equation:
$$ W = W_{sat,WBT} - \\frac{c_{pa}(T - T_{wb})}{h_{fg,WBT}} $$
*(Where $W_{sat,WBT}$ is the humidity ratio at saturation at WBT, and $h_{fg,WBT}$ is the latent heat at that temperature)*

**7. Dew Point Temperature ($T_{dp}$)**
$$ T_{dp} = \\frac{243.04 \\times \\ln(P_w / 611.2)}{17.625 - \\ln(P_w / 611.2)} $$

---

### 🔄 Process Analysis Principles

**Sensible Heat Factor (SHF)**
Represents the ratio of sensible to total cooling load:
$$ SHF = \\frac{Q_{sensible}}{Q_{total}} = \\frac{1.006 \\times \\Delta T}{1.006 \\times \\Delta T + \\Delta W \\times 2501} $$

**Apparatus Dew Point (ADP) & Bypass Factor**
For cooling and dehumidification, ADP represents the effective coil surface temperature:
$$ ADP = T_{coil} \\approx T_{outlet} - BF \\times (T_{inlet} - T_{outlet}) $$
*(Where Bypass Factor $BF$ represents the fraction of air that bypasses the coil without contacting it)*

**Adiabatic Mixing**
The mixed state is determined by conservation of mass and energy:
$$ W_{mix} = \\frac{\\dot{m}_1 W_1 + \\dot{m}_2 W_2}{\\dot{m}_1 + \\dot{m}_2} $$
$$ h_{mix} = \\frac{\\dot{m}_1 h_1 + \\dot{m}_2 h_2}{\\dot{m}_1 + \\dot{m}_2} $$
$$ T_{mix} = \\frac{h_{mix} - 2501 \\times W_{mix}}{1.006 + 1.86 \\times W_{mix}} $$

**Evaporative Cooling**
This process follows a constant Wet Bulb Temperature ($T_{wb}$) line on the psychrometric chart. Driven by saturation efficiency:
$$ \\eta_{sat} = \\frac{T_{in} - T_{out}}{T_{in} - T_{wb,in}} \\times 100\\% $$

---

### 📦 Core Engineering Stack

Our platform leverages industry-standard data and engineering libraries:
- **`psychrolib`**: The core calculation engine, directly implementing the ASHRAE Handbook Fundamentals algorithms for precise psychrometric properties.
- **`numpy`**: Provides fast, vectorized array operations for generating the non-linear saturation curves and thermodynamic bounds.
- **`pandas`**: Structures simulation sequences and tabular data for reports.
- **`plotly`**: Renders the high-performance, interactive, layered psychrometric SVG charts.
- **`streamlit`**: Powers the dynamic web interface, real-time reactive state, and Neo-Brutalist/Glassmorphic component updates.
    """)

def render_header(colors):
    """Renders the HTML-based header bar."""
    bg = colors["bg"]
    text_pri = colors["text_primary"]
    text_sec = colors["text_secondary"]
    card_bg = colors["card_bg"]
    border = colors["border"]
    shadow = colors["shadow"]
    accent = colors["accent"]

    col1, col2 = st.columns([1.5, 1], vertical_alignment="center")
    
    with col1:
        html_left = (
            "<div style='background-color: transparent; width: 100%; padding: 12px 24px; "
            "display: flex; justify-content: flex-start; align-items: center;'>"
            "  <div>"
            "    <div style='font-family: Inter, sans-serif; font-weight: 700; font-size: 20px; "
            "color: " + text_pri + "; letter-spacing: 2px; text-transform: uppercase;'>"
            "PSYCHROMETRIC VISUALIZER</div>"
            "    <div style='font-family: Inter, sans-serif; font-weight: 400; font-size: 11px; "
            "color: " + text_sec + "; letter-spacing: 1px;'>"
            "ASHRAE-Validated Interactive Analysis Tool</div>"
            "  </div>"
            "</div>"
        )
        st.markdown(html_left, unsafe_allow_html=True)

    with col2:
        st.markdown(
            "<div style='display: flex; gap: 10px; justify-content: flex-end; padding-top: 12px; margin-bottom: 5px;'>"
            "  <span style='background-color: " + card_bg + "; border: 1px solid " + border + "; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; color: " + text_sec + "; "
            "font-family: JetBrains Mono, monospace; box-shadow: 0 1px 2px " + shadow + ";'>SI UNITS</span>"
            "  <span style='background-color: " + card_bg + "; border: 1px solid " + border + "; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; color: " + text_sec + "; "
            "font-family: JetBrains Mono, monospace; box-shadow: 0 1px 2px " + shadow + ";'>ASHRAE 2017</span>"
            "  <span style='background-color: " + card_bg + "; border: 1px solid " + border + "; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; color: " + text_sec + "; "
            "font-family: JetBrains Mono, monospace; box-shadow: 0 1px 2px " + shadow + ";'>PsychroLib v2</span>"
            "</div>",
            unsafe_allow_html=True
        )
        
        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col2:
            if st.button("📚 Guide & Formulas", key="guide_btn"):
                show_guide_dialog()

    st.markdown("<hr style='margin: 0; padding: 0; border: none; height: 1px; background-color: " + border + ";'>", unsafe_allow_html=True)


def render_state_panel(state_dict, label, color, colors, delta_state=None, is_outlet=False):
    """Renders the properties cards for an air state."""
    st.markdown(
        "<div style='color: " + color + "; font-family: Inter, sans-serif; "
        "font-weight: 600; font-size: 13px; letter-spacing: 1px; margin-bottom: 15px;'>"
        "◉ " + label + "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    def render_metric(col_ref, title, value_fmt, val, d_val, inverse=False):
        c_mode = "inverse" if inverse else "normal"
        with col_ref:
            if d_val is not None:
                d_str = f"{val - d_val:.2g}"
                st.metric(title, value_fmt, delta=d_str, delta_color=c_mode)
            else:
                st.metric(title, value_fmt)

    with col1:
        render_metric(col1, "Dry Bulb Temp (°C)",
                      f"{state_dict['DBT']:.1f}", state_dict['DBT'],
                      delta_state['DBT'] if delta_state else None, inverse=True)
        render_metric(col1, "Relative Humidity (%)",
                      f"{state_dict['RH']:.1f}", state_dict['RH'],
                      delta_state['RH'] if delta_state else None, inverse=True)
        render_metric(col1, "Enthalpy (kJ/kg)",
                      f"{state_dict['h']:.2f}", state_dict['h'],
                      delta_state['h'] if delta_state else None, inverse=True)

    with col2:
        render_metric(col2, "Wet Bulb Temp (°C)",
                      f"{state_dict['WBT']:.1f}", state_dict['WBT'],
                      delta_state['WBT'] if delta_state else None, inverse=True)
        render_metric(col2, "Humidity Ratio (g/kg)",
                      f"{state_dict['W_gkg']:.3f}", state_dict['W_gkg'],
                      delta_state['W_gkg'] if delta_state else None, inverse=True)
        render_metric(col2, "Sp. Volume (m³/kg)",
                      f"{state_dict['v']:.4f}", state_dict['v'],
                      delta_state['v'] if delta_state else None, inverse=False)


def render_process_results(results_dict, process_type, process_color, description, colors):
    """Renders the calculation outputs panel specific to the selected process."""
    card_bg = colors["card_bg"]
    border = colors["border"]
    text_sec = colors["text_secondary"]
    text_pri = colors["text_primary"]
    shadow = colors["shadow"]

    st.markdown(
        "<div style='color: " + process_color + "; font-family: Inter, sans-serif; "
        "font-weight: 600; font-size: 13px; letter-spacing: 1px; margin-bottom: 15px;'>"
        "⟶ PROCESS ANALYSIS</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='background-color: " + card_bg + "; border-radius: 8px; "
        "padding: 15px; box-shadow: 0 4px 6px " + shadow + ";'>",
        unsafe_allow_html=True,
    )

    for key, value in results_dict.items():
        row_html = (
            "<div style='display: flex; justify-content: space-between; "
            "margin-bottom: 10px; border-bottom: 1px solid " + border + "; padding-bottom: 6px;'>"
            "<span style='color: " + text_sec + "; font-size: 12px; "
            "font-family: Inter, sans-serif;'>" + str(key) + "</span>"
            "<span style='color: " + text_pri + "; font-size: 13px; "
            "font-family: JetBrains Mono, monospace; font-weight: 600;'>" + str(value) + "</span>"
            "</div>"
        )
        st.markdown(row_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='margin-top: 15px; font-family: Inter, sans-serif; font-size: 12px; "
        "color: " + text_sec + "; font-style: italic; line-height: 1.5; padding: 4px;'>"
        + description + "</div>",
        unsafe_allow_html=True,
    )
