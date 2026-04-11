# Psychrometric Process Visualizer — User Guide

This application is a professional engineering tool for visualizing common psychrometric processes on an interactive ASHRAE-aligned chart.

## Prerequisites

- **Python 3.9+** installed on your system.
- Basic understanding of psychrometrics (Dry Bulb Temperature, Relative Humidity, etc.).

## 🚀 How to Run on Localhost

1. **Navigate to the project directory**:
   ```powershell
   cd "c:\Users\balaj\OneDrive\Desktop\PBL projects\RAC\psychro_visualizer"
   ```

2. **Install Dependencies**:
   Ensure you have the required libraries installed via the `requirements.txt` file:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Launch the Application**:
   Run the Streamlit server:
   ```powershell
   streamlit run app.py
   ```

4. **Access the Portal**:
   Once running, open your browser and go to:
   `http://localhost:8501`

---

## 🛠️ How to Use the Visualizer

### 1. Select Process Type
In the left sidebar, choose from 6 different psychrometric processes:
- **Sensible Heating/Cooling**: For pure temperature changes.
- **Cooling & Dehumidification**: Standard AC cooling coil analysis.
- **Heating & Humidification**: Winter conditioning.
- **Evaporative Cooling**: Adiabatic cooling following constant Wet Bulb lines.
- **Adiabatic Mixing**: Mixing two different air streams.

### 2. Configure States
- Use the sliders to set your **Inlet Air State** (DBT and RH).
- Depending on the process, set the **Outlet Air State** or **Target Conditions**.
- Changes are reflected in the sidebar value readouts in real-time.

### 3. Chart Options
Toggle the visibility of background reference lines to declutter the view:
- **RH Lines**: Constant relative humidity curves.
- **Enthalpy Lines**: Constant energy content lines.
- **Comfort Zone**: The ASHRAE standard human comfort box.

### 4. Analyze Results
Click **CALCULATE PROCESS** to:
- Generate the process line and direction arrows on the chart.
- Populate the **State Panels** (Inlet/Outlet) with all 6 air properties.
- View the **Process Analysis** panel for engineering metrics (Sensible Heat Factor, Moisture Removed, Efficiency, etc.).

---

## 🧪 Validation & Error Handling
The tool enforces thermodynamic bounds:
- Temperatures restricted to **0°C to 50°C**.
- Relative Humidity between **5% and 95%**.
- Logical checks ensure, for example, that a "Heating" process doesn't result in a lower temperature than the inlet.

---
*Powered by PsychroLib · ASHRAE SI Units*
