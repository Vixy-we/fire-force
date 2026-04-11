"""
psychro_calc.py

Core calculation engine for the psychrometric visualizer.
Provides state definition and process calculations with thermodynamic validations.
"""

import math
import psychrolib

# Initialize PsychroLib to use SI units
psychrolib.SetUnitSystem(psychrolib.SI)

# Thermodynamic Constants
C_PA = 1.006    # Specific heat of dry air, kJ/kg*K
H_FG = 2501.0   # Latent heat of vaporization at 0 degC, kJ/kg
C_PV = 1.86     # Specific heat of water vapour, kJ/kg*K
P_ATM = 101325.0 # Standard atmospheric pressure in Pa

def calculate_state(DBT, RH):
    """
    Calculate full psychrometric properties for a given state.

    Args:
        DBT (float): Dry bulb temperature in °C
        RH (float): Relative humidity in %

    Returns:
        dict: Complete state dictionary with keys DBT, WBT, RH, W, W_gkg, h, v.
    """
    # Clamp RH to valid physical bounds [0, 100] then convert to decimal [0, 1]
    RH = max(0.0, min(100.0, RH))
    RH_decimal = RH / 100.0
    RH_decimal = max(0.0, min(1.0, RH_decimal))
    
    # Wet Bulb Temperature
    WBT = psychrolib.GetTWetBulbFromRelHum(DBT, RH_decimal, P_ATM)
    
    # Humidity Ratio (kg/kg)
    W = psychrolib.GetHumRatioFromRelHum(DBT, RH_decimal, P_ATM)
    W_gkg = W * 1000.0
    
    # Enthalpy (PsychroLib returns J/kg dry air)
    h_J_kg = psychrolib.GetMoistAirEnthalpy(DBT, W)
    h = h_J_kg / 1000.0
    
    # Specific Volume (m3/kg)
    v = psychrolib.GetMoistAirVolume(DBT, W, P_ATM)
    
    return {
        "DBT": DBT,
        "WBT": WBT,
        "RH": RH,
        "W": W,
        "W_gkg": W_gkg,
        "h": h,
        "v": v
    }

def validate_state(DBT, RH, inlet_DBT=None, inlet_RH=None, process_type=None, target_RH=None):
    """
    Validate inputs to ensure physical possibility based on project rules.

    Args:
        DBT (float): Dry bulb temperature in °C
        RH (float): Relative humidity in %
        inlet_DBT (float): Inlet DBT for relative rules
        inlet_RH (float): Inlet RH for relative rules
        process_type (str): Process type to apply specific rules
        target_RH (float): Target RH for evaporative cooling

    Returns:
        tuple: (bool is_valid, str error_message)
    """
    if not (0.0 <= DBT <= 50.0):
        return False, "Dry Bulb Temperature must be between 0°C and 50°C."
        
    if not (5.0 <= RH <= 95.0):
        return False, "Relative Humidity must be between 5% and 95%."
        
    if process_type:
        if process_type == "Sensible Cooling":
            if DBT >= inlet_DBT:
                return False, "For Sensible Cooling, Outlet DBT must be less than Inlet DBT."
        elif process_type == "Sensible Heating":
            if DBT <= inlet_DBT:
                return False, "For Sensible Heating, Outlet DBT must be greater than Inlet DBT."
        elif process_type == "Cooling & Dehumidification":
            if DBT >= inlet_DBT:
                return False, "Outlet DBT must be less than Inlet DBT."
            inlet_W = psychrolib.GetHumRatioFromRelHum(inlet_DBT, inlet_RH / 100.0, P_ATM)
            outlet_W = psychrolib.GetHumRatioFromRelHum(DBT, RH / 100.0, P_ATM)
            if outlet_W > inlet_W:
                return False, "Outlet humidity ratio must not exceed inlet humidity ratio for dehumidification."
        elif process_type == "Heating & Humidification":
            if DBT <= inlet_DBT:
                return False, "Outlet DBT must be greater than Inlet DBT."
            inlet_W = psychrolib.GetHumRatioFromRelHum(inlet_DBT, inlet_RH / 100.0, P_ATM)
            outlet_W = psychrolib.GetHumRatioFromRelHum(DBT, RH / 100.0, P_ATM)
            if outlet_W < inlet_W:
                return False, "Outlet moisture must be greater than inlet moisture."
        elif process_type == "Evaporative Cooling":
            if target_RH is not None and target_RH <= inlet_RH:
                return False, "Target RH must be greater than Inlet RH for Evaporative Cooling."
                
    return True, ""

def calculate_process(inlet_state, outlet_state, process_type, mass_ratio=None):
    """
    Calculate specific engineering outputs for a given process type.

    Args:
        inlet_state (dict): State dictionary for inlet
        outlet_state (dict): State dictionary for outlet
        process_type (str): Name of process type
        mass_ratio (float): Optional parameter for mixing process

    Returns:
        dict: Process engineering outputs formatted for display.
    """
    results = {}
    
    delta_h = outlet_state["h"] - inlet_state["h"]
    delta_T = outlet_state["DBT"] - inlet_state["DBT"]
    delta_W = outlet_state["W"] - inlet_state["W"]
    delta_W_gkg = outlet_state["W_gkg"] - inlet_state["W_gkg"]
    
    if process_type in ["Sensible Heating", "Sensible Cooling"]:
        # Sensible Heat added/removed (kJ/kg)
        results["Sensible Heat Added/Removed (kJ/kg)"] = round(abs(delta_h), 2)
        results["Temperature Change (°C)"] = round(abs(delta_T), 1)
        results["Process Direction"] = "Heating" if delta_T > 0 else "Cooling"
        
    elif process_type == "Cooling & Dehumidification":
        sensible_heat = C_PA * abs(delta_T)
        latent_heat = H_FG * abs(delta_W)
        total_load = abs(delta_h)
        
        shf = sensible_heat / total_load if total_load > 0 else 1.0
        
        results["Total Cooling Load (kJ/kg)"] = round(total_load, 2)
        results["Sensible Heat Removed (kJ/kg)"] = round(sensible_heat, 2)
        results["Latent Heat Removed (kJ/kg)"] = round(latent_heat, 2)
        results["Moisture Removed (g/kg)"] = round(abs(delta_W_gkg), 2)
        results["Sensible Heat Factor (SHF)"] = round(shf, 3)
        # Approximate ADP calculation could go here, but omitted for simplicity
        results["Apparatus Dew Point (ADP)"] = round(psychrolib.GetTDewPointFromRelHum(outlet_state["DBT"], outlet_state["RH"]/100.0), 1) # simple approx
        
    elif process_type == "Evaporative Cooling":
        # Saturation efficiency: (T_in - T_out)/(T_in - T_wb)
        T_wb_in = inlet_state["WBT"]
        if abs(inlet_state["DBT"] - T_wb_in) > 0.001:
            eff = (inlet_state["DBT"] - outlet_state["DBT"]) / (inlet_state["DBT"] - T_wb_in) * 100
        else:
            eff = 100.0
            
        results["Temperature Drop (°C)"] = round(abs(delta_T), 1)
        results["Humidity Increase (g/kg)"] = round(abs(delta_W_gkg), 2)
        results["Saturation Efficiency (%)"] = round(eff, 1)
        
    elif process_type == "Adiabatic Mixing of Two Streams":
        results["Mixed State DBT (°C)"] = round(outlet_state["DBT"], 1)
        results["Mixed State RH (%)"] = round(outlet_state["RH"], 1)
        results["Mixed State Enthalpy (kJ/kg)"] = round(outlet_state["h"], 2)
        results["Stream 1 Contribution (%)"] = round((mass_ratio or 0.5) * 100, 0)
        results["Stream 2 Contribution (%)"] = round((1.0 - (mass_ratio or 0.5)) * 100, 0)
        
    elif process_type == "Heating & Humidification":
        results["Heat Added (kJ/kg)"] = round(abs(delta_h), 2)
        results["Moisture Added (g/kg)"] = round(abs(delta_W_gkg), 2)
        results["Total Enthalpy Change (kJ/kg)"] = round(abs(delta_h), 2)

    return results

def calculate_mixed_state(state1, state2, m1_ratio):
    """
    Calculate the resulting state from adiabatically mixing two air streams.
    Uses mass conservation for moisture and energy conservation for enthalpy.
    """
    m2_ratio = 1.0 - m1_ratio
    mixed_h = m1_ratio * state1["h"] + m2_ratio * state2["h"]
    mixed_w = m1_ratio * state1["W"] + m2_ratio * state2["W"]
    
    mixed_h_J = mixed_h * 1000.0
    
    # PsychroLib: GetTDryBulbFromEnthalpyAndHumRatio
    mixed_T = psychrolib.GetTDryBulbFromEnthalpyAndHumRatio(mixed_h_J, mixed_w)
    mixed_RH = psychrolib.GetRelHumFromHumRatio(mixed_T, mixed_w, P_ATM) * 100.0
    # Clamp to physical bounds to prevent downstream psychrolib errors
    mixed_RH = max(0.0, min(100.0, mixed_RH))
    
    return calculate_state(mixed_T, mixed_RH)

def calculate_evaporative_cooling_state(inlet_state, target_RH):
    """
    Calculate outlet state for evaporative cooling, which follows a constant WBT line.
    Calculates the intersection of the constant inlet WBT line and target RH curve.
    """
    WBT_target = inlet_state["WBT"]
    target_RH_dec = target_RH / 100.0
    
    # Iterative method to find DBT where WBT equals inlet WBT at target RH
    T_high = inlet_state["DBT"]
    T_low = WBT_target
    DBT_out = T_high
    
    for _ in range(30):
        T_mid = (T_high + T_low) / 2.0
        wbt_guess = psychrolib.GetTWetBulbFromRelHum(T_mid, target_RH_dec, P_ATM)
        if wbt_guess > WBT_target:
            T_high = T_mid
        else:
            T_low = T_mid
        DBT_out = T_mid
            
    return calculate_state(DBT_out, target_RH)
