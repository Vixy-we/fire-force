# Psychrometric Visualizer

**Psychrometric Visualizer** is a web application that visualizes air conditioning processes on a psychrometric chart. It allows users to simulate air handling unit (AHU) cycles, explore thermodynamic properties of air-water mixtures, and understand HVAC concepts through interactive charts and animations.

## Features

- **Interactive Psychrometric Chart**: Plotting of dry-bulb temperature vs. humidity ratio with:
  - Saturation curve
  - Isotherms (constant dry-bulb temperature)
  - Isohygrics (constant humidity ratio)
  - Isotherms (constant wet-bulb temperature)
  - Isenthalps (constant enthalpy)
  - Constant relative humidity curves
- **AHU Simulation**: Step-by-step simulation of air through an Air Handling Unit with:
  - Outdoor air intake
  - Mixing with return air
  - Cooling coil process
  - Fan heat addition
  - Supply air delivery
- **Real-time Updates**: All charts and values update instantly as parameters change
- **Energy Analysis**: Calculation and display of:
  - Sensible heat
  - Latent heat
  - Total heat
  - Sensible heat factor (SHF)
  - Cooling coil load
- **Multiple Input Modes**: Support for:
  - Dry-bulb temperature and relative humidity
  - Dry-bulb temperature and wet-bulb temperature
  - Dry-bulb temperature and humidity ratio
- **Theme Support**: Toggle between light and dark modes
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd psychro_visualizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the Application

Start the Streamlit server from the project directory:

```bash
streamlit run psychro_visualizer/main.py
```

The application will open automatically in your web browser.

### Navigate Between Pages

Use the sidebar navigation to switch between:

- **Home**: Introduction and overview
- **Chart**: Interactive psychrometric chart
- **Simulation**: AHU process simulation

## Project Structure

```
psychro_visualizer/
├── main.py                 # Main application entry point
├── psychro_calc.py         # Psychrometric calculation logic
├── chart.py                # Chart visualization functions
├── ui_components.py        # UI components and layout
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
└── .gitignore              # Files to ignore in version control
```

## Development

### Adding New Features

1. **Update calculations**: Modify `psychro_calc.py` for new thermodynamic models
2. **Add UI components**: Create new pages in `main.py` or add components to `ui_components.py`
3. **Update charts**: Modify `chart.py` for new visualization types
4. **Test changes**: Run `streamlit run psychro_visualizer/main.py` to test

### Code Style

- Use descriptive variable names
- Add comments for complex calculations
- Follow PEP 8 style guidelines
- Keep functions focused and modular

## License

This project is licensed under the terms of the MIT license.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on the GitHub repository.

---

**Built with Streamlit and PsychroLib**
