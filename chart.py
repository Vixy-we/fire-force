"""
chart.py

Constructs the psychrometric chart using Plotly.
Builds the base figure with all psychrometric lines, and dynamic state markers.
"""
import numpy as np
import plotly.graph_objects as go
import psychrolib

# Ensure PsychroLib uses SI
psychrolib.SetUnitSystem(psychrolib.SI)
P_ATM = 101325.0

def build_psychro_chart(config, colors):
    fig = go.Figure()
    
    # Base layout
    fig.update_layout(
        plot_bgcolor=colors["bg"],
        paper_bgcolor=colors["bg"],
        xaxis=dict(
            title=dict(text="Dry Bulb Temperature (°C)", font=dict(color=colors["text_secondary"], family="Inter", size=12)),
            range=[0, 50],
            gridcolor=colors["grid"],
            gridwidth=1,
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"], family="JetBrains Mono", size=10)
        ),
        yaxis=dict(
            title=dict(text="Humidity Ratio — ω (kg/kg dry air)", font=dict(color=colors["text_secondary"], family="Inter", size=12)),
            range=[0, 0.030],
            gridcolor=colors["grid"],
            gridwidth=1,
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"], family="JetBrains Mono", size=10)
        ),
        margin=dict(l=60, r=40, t=20, b=60),
        height=520,
        showlegend=False
    )
    
    # STEP 1 — Saturation Curve
    T_sat = np.arange(0, 50.5, 0.5)
    W_sat = [psychrolib.GetHumRatioFromRelHum(t, 1.0, P_ATM) for t in T_sat]
    
    fig.add_trace(go.Scatter(
        x=T_sat, y=W_sat,
        mode="lines",
        line=dict(color=colors["accent"], width=2.5),
        name="Saturation Curve",
        hoverinfo="skip",
        fill="tozeroy",
        fillcolor="rgba(0, 201, 255, 0.04)"
    ))
    
    # STEP 2 — RH Lines
    if config.get("Show RH Lines", True):
        for rh in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            W_rh = [psychrolib.GetHumRatioFromRelHum(t, rh, P_ATM) for t in T_sat]
            fig.add_trace(go.Scatter(
                x=T_sat, y=W_rh,
                mode="lines",
                line=dict(color=colors["rh_line"], width=1, dash="dot"),
                name=f"{int(rh*100)}% RH",
                hoverinfo="skip"
            ))
            
            # Label at right bound
            W_label = psychrolib.GetHumRatioFromRelHum(48, rh, P_ATM)
            if W_label <= 0.029:
                fig.add_trace(go.Scatter(
                    x=[48], y=[W_label + 0.0005],
                    mode="text",
                    text=[f"{int(rh*100)}%"],
                    textfont=dict(color=colors["text_secondary"], size=9, family="JetBrains Mono"),
                    hoverinfo="skip"
                ))

    # STEP 3 — Constant Enthalpy Lines
    if config.get("Show Enthalpy Lines", True):
        for h in [20, 30, 40, 50, 60, 70, 80]:
            W_h = []
            T_h = []
            for t in T_sat:
                # Based on h = 1.006*T + W*(2501 + 1.86*T)
                w_val = (h - 1.006 * t) / (2501 + 1.86 * t)
                w_sat_val = psychrolib.GetHumRatioFromRelHum(t, 1.0, P_ATM)
                if w_val >= 0 and w_val <= w_sat_val * 1.05:
                    W_h.append(w_val)
                    T_h.append(t)
            
            if W_h:
                fig.add_trace(go.Scatter(
                    x=T_h, y=W_h,
                    mode="lines",
                    line=dict(color=colors["h_line"], width=1, dash="dash"),
                    name=f"h={h}",
                    hoverinfo="skip"
                ))
    
    # STEP 4 — Constant WBT Lines
    if config.get("Show WBT Lines", False):
        for wbt in [10, 15, 20, 25, 30]:
            W_wbt = []
            T_wbt = []
            for t in np.arange(wbt, 50.5, 0.5):
                try:
                    w_val = psychrolib.GetHumRatioFromTWetBulb(t, wbt, P_ATM)
                    w_sat_val = psychrolib.GetHumRatioFromRelHum(t, 1.0, P_ATM)
                    if w_val >= 0 and w_val <= w_sat_val * 1.01:
                        W_wbt.append(w_val)
                        T_wbt.append(t)
                except Exception:
                    pass
            if W_wbt:
                fig.add_trace(go.Scatter(
                    x=T_wbt, y=W_wbt,
                    mode="lines",
                    line=dict(color=colors["wbt_line"], width=1, dash="longdash"),
                    hoverinfo="skip"
                ))

    # STEP 5 — ASHRAE Comfort Zone
    if config.get("Show Comfort Zone", True):
        cz_T = [20, 26, 26, 20, 20]
        cz_W = [0.004, 0.004, 0.012, 0.012, 0.004]
        fig.add_trace(go.Scatter(
            x=cz_T, y=cz_W,
            mode="lines",
            fill="toself",
            fillcolor="rgba(0, 230, 118, 0.06)",
            line=dict(color="#00E676", width=1.5, dash="dot"),
            name="ASHRAE Comfort Zone",
            hoverinfo="skip"
        ))
        
        fig.add_trace(go.Scatter(
            x=[23], y=[0.008],
            mode="text",
            text=["COMFORT ZONE"],
            textfont=dict(color="#00E676", size=9, family="JetBrains Mono"),
            hoverinfo="skip"
        ))
        
    return fig

def add_state_points(fig, inlet, outlet, process_name, process_color, colors):
    """
    Add state markers and process line to an existing psychrometric chart figure.
    """
    # STEP 6 — State Points tooltips setup
    inlet_cd = [inlet["DBT"], inlet["WBT"], inlet["RH"], inlet["W"], inlet["h"], inlet["v"]]
    outlet_cd = [outlet["DBT"], outlet["WBT"], outlet["RH"], outlet["W"], outlet["h"], outlet["v"]]
    
    template = (
        "DBT: %{customdata[0]:.1f} °C<br>"
        "WBT: %{customdata[1]:.1f} °C<br>"
        "RH: %{customdata[2]:.1f} %<br>"
        "ω: %{customdata[3]:.4f} kg/kg<br>"
        "h: %{customdata[4]:.2f} kJ/kg<br>"
        "v: %{customdata[5]:.4f} m³/kg"
    )

    # STEP 7 — Process Line
    fig.add_trace(go.Scatter(
        x=[inlet["DBT"], outlet["DBT"]],
        y=[inlet["W"], outlet["W"]],
        mode="lines",
        line=dict(color=process_color, width=2.5),
        name=process_name,
        hoverinfo="skip"
    ))
    
    # Arrow annotation
    mid_x = (inlet["DBT"] + outlet["DBT"]) / 2.0
    mid_y = (inlet["W"] + outlet["W"]) / 2.0
    
    fig.add_annotation(
        x=outlet["DBT"], y=outlet["W"],
        ax=mid_x, ay=mid_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowcolor=process_color,
        arrowsize=1.5
    )

    # Outlet Marker
    fig.add_trace(go.Scatter(
        x=[outlet["DBT"]],
        y=[outlet["W"]],
        mode="markers+text",
        marker=dict(color=process_color, size=12, symbol="circle", line=dict(color="#FFFFFF", width=2)),
        text=["OUT"],
        textposition="top center",
        textfont=dict(family="JetBrains Mono", size=10, color=colors["text_primary"]),
        customdata=[outlet_cd],
        hovertemplate=template,
        name="Outlet State"
    ))

    # Inlet Marker
    fig.add_trace(go.Scatter(
        x=[inlet["DBT"]],
        y=[inlet["W"]],
        mode="markers+text",
        marker=dict(color=colors["accent"], size=12, symbol="circle", line=dict(color="#FFFFFF", width=2)),
        text=["IN"],
        textposition="top center",
        textfont=dict(family="JetBrains Mono", size=10, color=colors["text_primary"]),
        customdata=[inlet_cd],
        hovertemplate=template,
        name="Inlet State"
    ))
    
    return fig
