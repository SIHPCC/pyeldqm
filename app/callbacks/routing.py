"""
Tab routing callback — renders sidebar + content for each active tab.
"""
from dash import Input, Output, html


def register(app):
    from ..layout.sidebar import create_threat_zones_sidebar
    from ..components.tabs.threat_zones import create_threat_zones_content
    from ..components.tabs.par_analysis import create_par_content
    from ..components.tabs.route_optimization import create_route_optimization_content
    from ..components.tabs.sensor_placement import create_sensor_placement_content
    from ..components.tabs.health_impact import create_health_impact_content
    from ..components.tabs.shelter_analysis import create_shelter_analysis_content
    from ..components.tabs.about import create_about_content
    import dash_bootstrap_components as dbc

    @app.callback(
        Output("tab-content", "children"),
        Input("main-tabs", "active_tab"),
    )
    def render_tab_content(active_tab):
        """Render content based on active tab."""
        if active_tab == "tab-threat-zones":
            return dbc.Row([
                dbc.Col(create_threat_zones_sidebar(), width=3, style={"padding": 0}),
                create_threat_zones_content(),
            ])

        elif active_tab == "tab-par-analysis":
            return dbc.Row([
                dbc.Col(
                    create_threat_zones_sidebar(title="PAR Parameters", is_par_analysis=True),
                    width=3, style={"padding": 0},
                ),
                create_par_content(),
            ])

        elif active_tab == "tab-route-optimization":
            return dbc.Row([
                dbc.Col(
                    create_threat_zones_sidebar(
                        title="Emergency Routes Parameters", is_route_analysis=True
                    ),
                    width=3, style={"padding": 0},
                ),
                create_route_optimization_content(),
            ])

        elif active_tab == "tab-sensor-placement":
            return dbc.Row([
                dbc.Col(
                    create_threat_zones_sidebar(
                        title="Sensor Placement Parameters", is_sensor_analysis=True
                    ),
                    width=3, style={"padding": 0},
                ),
                create_sensor_placement_content(),
            ])

        elif active_tab == "tab-health-impact":
            return dbc.Row([
                dbc.Col(
                    create_threat_zones_sidebar(
                        title="Health Impact Parameters", is_health_impact_analysis=True
                    ),
                    width=3, style={"padding": 0},
                ),
                create_health_impact_content(),
            ])

        elif active_tab == "tab-shelter-analysis":
            return dbc.Row([
                dbc.Col(
                    create_threat_zones_sidebar(
                        title="Shelter Status Parameters", is_shelter_analysis=True
                    ),
                    width=3, style={"padding": 0},
                ),
                create_shelter_analysis_content(),
            ])

        elif active_tab == "tab-about":
            return dbc.Row([create_about_content()])

        # Default fallback
        return html.Div([
            html.H4("Select a tab to begin analysis"),
            html.P("Choose from the available analysis options above."),
        ])
