"""
Weather input components for Dash GUI.
"""

from dash import html
from .slider_controls import create_slider_with_range_control


def create_weather_manual_inputs() -> html.Div:
    """Create manual weather input sliders for the Threat Zones tab."""
    return html.Div([
        create_slider_with_range_control(
            "wind-speed", "Wind Speed (m/s)",
            0.1, 15, 2.5, 0.1,
            {0: '0', 5: '5', 10: '10', 15: '15'},
        ),
        create_slider_with_range_control(
            "wind-direction", "Wind Direction (degrees)",
            0, 360, 90, 5,
            {0: '0°', 90: '90°', 180: '180°', 270: '270°', 360: '360°'},
        ),
        create_slider_with_range_control(
            "temperature", "Temperature (°C)",
            -30, 60, 25, 1,
            {-30: '-30', 0: '0', 30: '30', 60: '60'},
        ),
        create_slider_with_range_control(
            "humidity", "Humidity (%)",
            0, 100, 65, 5,
            {0: '0', 50: '50', 100: '100'},
        ),
        create_slider_with_range_control(
            "cloud-cover", "Cloud Cover (%)",
            0, 100, 30, 10,
            {0: '0', 50: '50', 100: '100'},
        ),
    ])


def create_par_weather_manual_inputs() -> html.Div:
    """Create manual weather input sliders for the PAR tab."""
    return html.Div([
        create_slider_with_range_control(
            "par-wind-speed", "Wind Speed (m/s)",
            0.1, 15, 2.5, 0.1,
            {0: '0', 5: '5', 10: '10', 15: '15'},
        ),
        create_slider_with_range_control(
            "par-wind-direction", "Wind Direction (degrees)",
            0, 360, 90, 5,
            {0: '0°', 90: '90°', 180: '180°', 270: '270°', 360: '360°'},
        ),
        create_slider_with_range_control(
            "par-temperature", "Temperature (°C)",
            -30, 60, 25, 1,
            {-30: '-30', 0: '0', 30: '30', 60: '60'},
        ),
        create_slider_with_range_control(
            "par-humidity", "Humidity (%)",
            0, 100, 65, 5,
            {0: '0', 50: '50', 100: '100'},
        ),
        create_slider_with_range_control(
            "par-cloud-cover", "Cloud Cover (%)",
            0, 100, 30, 10,
            {0: '0', 50: '50', 100: '100'},
        ),
    ])
