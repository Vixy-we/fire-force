"""
process_config.py

Configuration definitions for psychrometric processes.
Provides mapping of process name to its theme color, required inputs, and description.
"""

PROCESS_CONFIG = {
    "Sensible Heating": {
        "color": "#FF6B35",
        "inputs": ["inlet_DBT", "inlet_RH", "outlet_DBT"],
        "description": "Sensible heating involves adding heat to the air without adding or removing moisture. This process occurs in heating coils and electric heaters. The dry bulb temperature increases while the humidity ratio remains constant, resulting in a decrease in relative humidity."
    },
    "Sensible Cooling": {
        "color": "#00C9FF",
        "inputs": ["inlet_DBT", "inlet_RH", "outlet_DBT"],
        "description": "Sensible cooling involves removing heat from the air without changing its moisture content. This occurs when air passes over a cooling coil that is at a temperature above the air's dew point. The dry bulb temperature decreases, increasing the relative humidity."
    },
    "Cooling & Dehumidification": {
        "color": "#7B2FFF",
        "inputs": ["inlet_DBT", "inlet_RH", "outlet_DBT", "outlet_RH"],
        "description": "Cooling and dehumidification occur simultaneously when air passes over a cooling coil whose surface temperature is below the original dew point temperature of the air. Moisture condenses out of the air as the dry bulb temperature drops, commonly seen in summer AC systems."
    },
    "Heating & Humidification": {
        "color": "#FF3D5A",
        "inputs": ["inlet_DBT", "inlet_RH", "outlet_DBT", "outlet_RH"],
        "description": "Heating and humidification are used commonly in winter air conditioning where both sensible heat and moisture must be added to the conditioned space. The dry bulb temperature and humidity ratio both increase."
    },
    "Evaporative Cooling": {
        "color": "#00E676",
        "inputs": ["inlet_DBT", "inlet_RH", "target_RH"],
        "description": "Evaporative cooling is an adiabatic process where sensible heat from the air is used to evaporate water. It follows a constant wet bulb temperature line. The dry bulb temperature decreases as humidity ratio increases."
    },
    "Adiabatic Mixing of Two Streams": {
        "color": "#FFD700",
        "inputs": ["inlet_DBT", "inlet_RH", "DBT2", "RH2", "mass_ratio"],
        "description": "Adiabatic mixing involves combining two separate air streams into one without adding or removing heat. The resulting state lies on a straight line connecting the two initial states on the psychrometric chart, positioned according to their mass flow ratio."
    }
}
