"""About tab — professional & industrial-grade information panel."""

from dash import html
import dash_bootstrap_components as dbc
from ..styles import CARD_STYLE, CONTENT_STYLE


# ── colour palette consistent with the app theme ──────────────────────────────
_ACCENT   = "#1f77b4"
_DARK     = "#1a2a3a"
_MUTED    = "#6c757d"
_BG_LIGHT = "#f8f9fa"
_BORDER   = "#e9ecef"
_FONT     = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'


def _section_header(icon_cls: str, title: str, color: str = _ACCENT):
    return html.Div([
        html.I(className=icon_cls, style={"marginRight": "0.55rem", "color": color, "fontSize": "1rem"}),
        html.Span(title, style={"fontWeight": "700", "fontSize": "1rem", "letterSpacing": "0.4px", "color": _DARK}),
    ], style={
        "display": "flex", "alignItems": "center",
        "borderBottom": f"2px solid {color}",
        "paddingBottom": "0.45rem", "marginBottom": "1rem",
    })


def _capability_badge(icon_cls: str, label: str, bg: str = "#e8f0fe"):
    return dbc.Col(html.Div([
        html.I(className=icon_cls, style={"fontSize": "1.45rem", "color": _ACCENT, "marginBottom": "0.4rem"}),
        html.Div(label, style={"fontSize": "0.78rem", "fontWeight": "600", "color": _DARK, "textAlign": "center", "lineHeight": "1.3"}),
    ], style={
        "background": bg, "borderRadius": "10px", "padding": "0.85rem 0.6rem",
        "textAlign": "center", "minHeight": "90px",
        "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.08)", "border": f"1px solid {_BORDER}",
    }), width=6, md=4, lg=3, className="mb-3")


def _model_row(name: str, standard: str, desc: str, badge_color: str = "primary"):
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Badge(standard, color=badge_color, className="me-2", style={"fontSize": "0.7rem"}),
                    html.Span(name, style={"fontWeight": "700", "fontSize": "0.88rem", "color": _DARK}),
                ], style={"marginBottom": "0.2rem"}),
                html.Small(desc, style={"color": _MUTED, "fontSize": "0.8rem"}),
            ])
        ])
    ], style={"padding": "0.65rem 1rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"})


def _stat_card(value: str, label: str, icon_cls: str, color: str = _ACCENT):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.I(className=icon_cls, style={"fontSize": "1.6rem", "color": color, "marginBottom": "0.35rem"}),
            html.Div(value, style={"fontSize": "1.55rem", "fontWeight": "800", "color": _DARK, "lineHeight": "1.1"}),
            html.Div(label, style={"fontSize": "0.75rem", "color": _MUTED, "fontWeight": "500", "marginTop": "0.2rem"}),
        ], style={"textAlign": "center", "padding": "1rem 0.75rem"}),
    ], style={**CARD_STYLE, "border": f"1px solid {_BORDER}", "borderTop": f"3px solid {color}"}),
    width=6, md=4, lg=3, className="mb-3")


# ══════════════════════════════════════════════════════════════════════════════
def create_about_content():
    """Return the full About tab content column."""
    return dbc.Col([
        html.Div(style={"height": "0.75rem"}),

        # ── Hero banner ───────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Img(
                            src="/assets/pyELDQM_logo_v0.1.png",
                            style={
                                "width": "100px",
                                "height": "100px",
                                "objectFit": "contain",
                                "transform": "scale(2.75)",
                                "transformOrigin": "center",
                                "display": "block",
                            },
                            alt="pyELDQM logo",
                        ),
                    ], width="auto", className="d-flex align-items-center",
                       style={"overflow": "visible", "marginRight": "1.5rem"}),
                    dbc.Col([
                        html.H2("pyELDQM", style={
                            "fontWeight": "900", "color": "#ffffff", "marginBottom": "0.1rem",
                            "fontSize": "2.1rem", "letterSpacing": "1px",
                        }),
                        html.Div("Emergency Leakage & Dispersion Quantification Modelling Toolkit", style={
                            "fontSize": "1.05rem", "fontWeight": "600", "color": "rgba(255,255,255,0.88)",
                            "marginBottom": "0.45rem", "letterSpacing": "0.3px",
                        }),
                        html.Div([
                            dbc.Badge("v 0.1.2", color="light", text_color="dark", className="me-2"),
                            dbc.Badge("MIT License", color="success", className="me-2"),
                            dbc.Badge("Python ≥ 3.10", color="info", text_color="dark", className="me-2"),
                            dbc.Badge("Open Source", color="warning", text_color="dark"),
                        ]),
                    ]),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fab fa-github me-2"),
                            "View on GitHub",
                        ], href="https://github.com/SIHPCC/pyeldqm", target="_blank",
                        color="light", outline=True, size="sm",
                        style={"fontWeight": "600", "borderRadius": "8px"}),
                    ], width="auto", className="d-flex align-items-center ms-auto"),
                ], align="center"),
            ], style={"padding": "1.5rem 2rem", "overflow": "visible"}),
        ], style={
            "background": f"linear-gradient(135deg, {_DARK} 0%, #1f3a5f 60%, #1f77b4 100%)",
            "border": "none", "borderRadius": "12px", "overflow": "visible",
            "boxShadow": "0 4px 18px rgba(31,119,180,0.25)", "marginBottom": "1.25rem",
        }),

        # ── At-a-glance stats ─────────────────────────────────────────────────
        dbc.Row([
            _stat_card("6+",   "Dispersion Models",      "fas fa-wind",          "#1f77b4"),
            _stat_card("5+",   "Chemical Source Models", "fas fa-flask",         "#d62728"),
            _stat_card("6",    "Analytical Modules",     "fas fa-th-large",      "#2ca02c"),
            _stat_card("AEGL", "Toxicology Standard",    "fas fa-shield-alt",    "#9467bd"),
        ], className="g-2"),

        # ── Overview ──────────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-info-circle", "Overview"),
                html.P([
                    html.Strong("pyELDQM"), " is an open-source, Python-based decision-support platform "
                    "designed for the rapid quantification of accidental or intentional chemical hazardous "
                    "material (HAZMAT) releases. It couples physics-based atmospheric dispersion modelling "
                    "with real-time weather data ingestion, geographic analysis, population exposure "
                    "estimation, and multi-criteria protective-action optimisation — all through an "
                    "interactive web dashboard built on Plotly Dash.",
                ], style={"fontSize": "0.9rem", "color": "#343a40", "lineHeight": "1.75", "marginBottom": "0.75rem"}),
                html.P(
                    "The toolkit is intended for use by emergency planners, industrial safety officers, "
                    "environmental consultants, and academic researchers who require a transparent, "
                    "auditable, and extensible consequence-modelling framework.",
                    style={"fontSize": "0.9rem", "color": "#343a40", "lineHeight": "1.75", "marginBottom": 0}),
            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Capabilities ──────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-cubes", "Core Capabilities"),
                dbc.Row([
                    _capability_badge("fas fa-cloud", "Gaussian & Heavy-Gas\nDispersion"),
                    _capability_badge("fas fa-fire", "Fire & Thermal\nRadiation Models"),
                    _capability_badge("fas fa-users", "Population At Risk\nAnalysis"),
                    _capability_badge("fas fa-route", "Emergency Route\nOptimisation"),
                    _capability_badge("fas fa-satellite-dish", "Optimal Sensor\nPlacement"),
                    _capability_badge("fas fa-home", "Shelter-in-Place\nAssessment"),
                    _capability_badge("fas fa-heartbeat", "AEGL/ERPG Health\nImpact Zones"),
                    _capability_badge("fas fa-cloud-sun", "Real-time Weather\nIngestion (OWM)"),
                ], className="g-2"),
            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Dispersion models ─────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-wind", "Implemented Dispersion & Source Models"),
                dbc.Row([
                    dbc.Col([
                        html.Div("Dispersion Models", style={
                            "fontWeight": "700", "fontSize": "0.82rem", "color": _MUTED,
                            "textTransform": "uppercase", "letterSpacing": "0.6px", "marginBottom": "0.5rem",
                        }),
                        dbc.ListGroup([
                            _model_row("Gaussian Plume",        "ISO 14687",    "Neutral-stability continuous release"),
                            _model_row("Pasquill-Gifford",      "US EPA",       "Stability-class-based Gaussian"),
                            _model_row("Dense / Heavy Gas",     "HEGADAS",      "Gravity-spread negatively-buoyant clouds"),
                            _model_row("Puff Dispersion",       "CAMEO/ALOHA",  "Time-varying instantaneous releases"),
                            _model_row("SLAB",                  "LLNL",         "Steady-state dense-gas model"),
                            _model_row("Multi-Phase Release",   "TNO Purple",   "Two-phase flashing jet / pool coupling"),
                        ], flush=True, style={"borderRadius": "6px", "border": f"1px solid {_BORDER}"}),
                    ], md=6),
                    dbc.Col([
                        html.Div("Source / Release Models", style={
                            "fontWeight": "700", "fontSize": "0.82rem", "color": _MUTED,
                            "textTransform": "uppercase", "letterSpacing": "0.6px", "marginBottom": "0.5rem",
                        }),
                        dbc.ListGroup([
                            _model_row("Pressurised Tank Rupture", "API 521",   "Liquid / vapour inventory blowdown"),
                            _model_row("Orifice / Pipe Leak",      "CCPS",      "Sub-sonic & choked orifice flow"),
                            _model_row("Pool Evaporation",         "SFPE",      "Evaporative mass-flux from liquid spill"),
                            _model_row("BLEVE / Fireball",         "TNO Yellow","Boiling-liquid expanding-vapour explosion"),
                            _model_row("VCE Overpressure",         "Baker-S.",  "Vapour-cloud explosion blast model"),
                            _model_row("Jet / Spray Release",      "PHAST",     "Free / impinging two-phase jet"),
                        ], flush=True, style={"borderRadius": "6px", "border": f"1px solid {_BORDER}"}),
                    ], md=6),
                ], className="g-3"),
            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Standards & compliance ─────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-certificate", "Standards & Compliance"),
                dbc.Row([
                    dbc.Col([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Strong("AEGL  ", style={"color": "#d62728"}),
                                "Acute Exposure Guideline Levels (US EPA / NAS) — Tier 1/2/3 thresholds"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("ERPG  ", style={"color": "#ff7f0e"}),
                                "Emergency Response Planning Guidelines (AIHA) — 1/2/3 levels"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("IDLH  ", style={"color": "#9467bd"}),
                                "Immediately Dangerous to Life or Health (NIOSH)"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("OSHA PEL / TLV  ", style={"color": "#2ca02c"}),
                                "Occupational exposure limits and threshold limit values (ACGIH)"
                            ], style={"fontSize": "0.85rem", "border": "none"}),
                        ], flush=True, style={"borderRadius": "6px", "border": f"1px solid {_BORDER}"}),
                    ], md=6),
                    dbc.Col([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Strong("Pasquill-Gifford Classes  ", style={"color": _ACCENT}),
                                "A–F atmospheric stability classification (US NWS)"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("IAEA Safety Series  "),
                                "Emergency preparedness and response guidance (IAEA GSR Part 7)"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("NFPA 704  "),
                                "Standard system for chemical hazard identification"
                            ], style={"fontSize": "0.85rem", "border": "none", "borderBottom": f"1px solid {_BORDER}"}),
                            dbc.ListGroupItem([
                                html.Strong("UN GHS  "),
                                "Globally Harmonised System of Classification and Labelling of Chemicals"
                            ], style={"fontSize": "0.85rem", "border": "none"}),
                        ], flush=True, style={"borderRadius": "6px", "border": f"1px solid {_BORDER}"}),
                    ], md=6),
                ], className="g-3"),
            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Technical stack ───────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-layer-group", "Technology Stack"),
                dbc.Row([
                    dbc.Col([
                        _tech_table("Computation", [
                            ("NumPy / SciPy",       "Numerical core — array ops & ODE solvers"),
                            ("pandas",              "Tabular data management"),
                            ("scikit-learn",        "Clustering & optimisation algorithms"),
                            ("scikit-image",        "Raster zone processing"),
                        ])
                    ], md=4),
                    dbc.Col([
                        _tech_table("Geospatial", [
                            ("GeoPandas / Shapely", "Vector geometry operations"),
                            ("pyproj",              "Coordinate reference system transforms"),
                            ("OSMnx / NetworkX",    "Street-network routing"),
                            ("rasterio",            "Raster terrain / DEM handling"),
                        ])
                    ], md=4),
                    dbc.Col([
                        _tech_table("Visualisation & UI", [
                            ("Plotly",              "Interactive scientific charts"),
                            ("Folium / Branca",     "Leaflet.js map tiles"),
                            ("Dash + DBC",          "Reactive web application framework"),
                            ("PyOWM",               "OpenWeatherMap live data"),
                        ])
                    ], md=4),
                ], className="g-3"),
            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Development team / affiliation ────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                _section_header("fas fa-users", "Development Team & Affiliation"),

                # Institutional affiliation banner
                html.Div([
                    dbc.Row([
                        dbc.Col(html.I(className="fas fa-university fa-2x",
                                       style={"color": _ACCENT}), width="auto",
                                className="d-flex align-items-center"),
                        dbc.Col([
                            html.Div("Shamim Irshad High Performance Computing Center (SIHPCC)", style={
                                "fontWeight": "800", "fontSize": "0.95rem", "color": _DARK,
                            }),
                            html.Div(
                                "Department of Chemical, Polymer & Composite Materials Engineering  ·  "
                                "University of Engineering & Technology (UET), Lahore, Pakistan",
                                style={"fontSize": "0.82rem", "color": _MUTED, "marginTop": "0.15rem"},
                            ),
                        ]),
                    ], align="center"),
                ], style={
                    "background": f"linear-gradient(90deg, #e8f0fe 0%, {_BG_LIGHT} 100%)",
                    "borderRadius": "10px", "padding": "1rem 1.4rem",
                    "border": f"1px solid #c5d8f6", "marginBottom": "1.25rem",
                }),

                # Principal Investigator
                html.Div("Principal Investigator", style={
                    "fontWeight": "700", "fontSize": "0.78rem", "color": _MUTED,
                    "textTransform": "uppercase", "letterSpacing": "0.7px", "marginBottom": "0.65rem",
                }),
                dbc.Row([
                    dbc.Col([
                        _contributor_card(
                            name="Dr. Zohaib Atiq Khan",
                            role="Principal Investigator & Project Lead",
                            designation="Assistant Professor",
                            dept="Department of Chemical, Polymer & Composite Materials Engineering",
                            institution="UET Lahore, Pakistan",
                            bio=(
                                "Dr. Zohaib Atiq Khan is an Assistant Professor in the Department of Chemical, "
                                "Polymer & Composite Materials Engineering at UET Lahore, where he heads the "
                                "Shamim Irshad High-Performance Computing (HPC) Centre and oversees the "
                                "development of pyELDQM and its underlying algorithms. Dr. Khan's research "
                                "focuses on process safety quantification, atmospheric dispersion modelling, "
                                "and consequence assessment for chemical hazard scenarios. A core pillar of "
                                "his work is the application of machine learning and high-performance computing "
                                "to complex engineering problems faced by industry — encompassing real-time "
                                "HAZMAT dispersion forecasting, risk-informed decision support, and "
                                "data-driven protective-action optimisation."
                            ),
                            badges=["Process Safety", "ML for Engineering", "HPC & AI", "Consequence Modelling"],
                            icon_color=_ACCENT,
                            border_color="#1f77b4",
                        ),
                    ], md=12),
                ], className="mb-3"),

                # Core contributors
                html.Div("Core Contributors", style={
                    "fontWeight": "700", "fontSize": "0.78rem", "color": _MUTED,
                    "textTransform": "uppercase", "letterSpacing": "0.7px",
                    "marginBottom": "0.65rem", "marginTop": "0.25rem",
                }),
                dbc.Row([
                    dbc.Col([
                        _contributor_card(
                            name="Research Team — SIHPCC",
                            role="Dispersion Modelling & Algorithm Development",
                            designation="Graduate Researchers & Engineers",
                            dept="Chemical, Polymer & Composite Materials Engineering",
                            institution="UET Lahore, Pakistan",
                            bio=(
                                "The SIHPCC research team is responsible for the implementation and "
                                "validation of atmospheric dispersion models, source-term estimation "
                                "algorithms, geospatial analysis modules, and the interactive Dash "
                                "application framework."
                            ),
                            badges=["Atmospheric Dispersion", "Source Modelling", "Geo-Analysis", "Dash UI"],
                            icon_color="#2ca02c",
                            border_color="#2ca02c",
                        ),
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-code-branch fa-2x",
                                   style={"color": "#9467bd", "marginBottom": "0.6rem"}),
                            html.Div("Open-Source Contributors", style={
                                "fontWeight": "700", "fontSize": "0.92rem", "color": _DARK,
                                "marginBottom": "0.3rem",
                            }),
                            html.P(
                                "pyELDQM welcomes contributions from the process-safety, environmental "
                                "engineering, and scientific Python communities. If you have implemented "
                                "a new dispersion model, extended the chemicals database, or improved the "
                                "application interface, please consider submitting a pull request.",
                                style={"fontSize": "0.82rem", "color": _MUTED,
                                       "lineHeight": "1.65", "marginBottom": "0.75rem"},
                            ),
                            dbc.Button([
                                html.I(className="fab fa-github me-2"),
                                "Contribute on GitHub",
                            ], href="https://github.com/SIHPCC/pyeldqm", target="_blank",
                            color="secondary", outline=True, size="sm",
                            style={"fontWeight": "600", "borderRadius": "6px", "fontSize": "0.8rem"}),
                        ], style={
                            "background": _BG_LIGHT, "borderRadius": "10px",
                            "padding": "1.1rem 1.4rem", "border": f"1px solid {_BORDER}",
                            "height": "100%",
                        }),
                    ], md=6),
                ], className="g-3"),

                # Citation / acknowledgement
                html.Div([
                    html.I(className="fas fa-quote-left",
                           style={"color": _MUTED, "marginRight": "0.5rem", "fontSize": "0.85rem"}),
                    html.Span("Citing pyELDQM", style={
                        "fontWeight": "700", "fontSize": "0.82rem",
                        "color": _DARK, "letterSpacing": "0.3px",
                    }),
                ], style={"marginTop": "1.25rem", "marginBottom": "0.4rem"}),
                html.Div(
                    "If you use pyELDQM in academic or industrial work, please cite the repository and "
                    "acknowledge the Shamim Irshad High Performance Computing Centre (SIHPCC), "
                    "University of Engineering & Technology (UET), Lahore, Pakistan.",
                    style={
                        "fontSize": "0.81rem", "color": _MUTED, "lineHeight": "1.65",
                        "background": _BG_LIGHT, "borderRadius": "8px",
                        "padding": "0.75rem 1rem", "border": f"1px solid {_BORDER}",
                        "borderLeft": f"3px solid {_ACCENT}",
                    }
                ),

            ], style={"padding": "1.25rem 1.5rem"}),
        ], style={**CARD_STYLE, "marginBottom": "1rem"}),

        # ── Disclaimer ────────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.I(className="fas fa-exclamation-triangle fa-2x",
                                   style={"color": "#856404"}), width="auto",
                            className="d-flex align-items-start pt-1"),
                    dbc.Col([
                        html.Div("Important Disclaimer", style={
                            "fontWeight": "700", "fontSize": "0.95rem", "color": "#533f03", "marginBottom": "0.35rem",
                        }),
                        html.Small(
                            "pyELDQM is provided for research, planning, and educational purposes only. "
                            "While the models implement established atmospheric dispersion and consequence "
                            "assessment methodologies, results are inherently dependent on input quality, "
                            "meteorological assumptions, and the limitations of the underlying mathematical "
                            "formulations. Model outputs should NOT be used as the sole basis for real-time "
                            "emergency response decisions without validation by a qualified process-safety "
                            "or environmental engineer. The authors accept no liability for decisions made "
                            "on the basis of this software.",
                            style={"color": "#533f03", "lineHeight": "1.7", "fontSize": "0.82rem"},
                        ),
                    ]),
                ], align="start"),
            ], style={"padding": "1.1rem 1.5rem"}),
        ], style={
            **CARD_STYLE,
            "background": "#fff8e1",
            "border": "1px solid #ffe082",
            "marginBottom": "1.5rem",
        }),

        html.Div(style={"height": "1rem"}),
    ], width=True, style={**CONTENT_STYLE, "fontFamily": _FONT})


# ── helper used only inside this module ───────────────────────────────────────
def _tech_table(title: str, rows: list):
    return html.Div([
        html.Div(title, style={
            "fontWeight": "700", "fontSize": "0.8rem", "color": _MUTED,
            "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "0.5rem",
        }),
        dbc.ListGroup([
            dbc.ListGroupItem([
                html.Span(lib, style={"fontWeight": "700", "fontSize": "0.83rem", "color": _DARK}),
                html.Small(f"  —  {desc}", style={"color": _MUTED}),
            ], style={"padding": "0.45rem 0.75rem", "border": "none",
                      "borderBottom": f"1px solid {_BORDER}"})
            for lib, desc in rows
        ], flush=True, style={"borderRadius": "6px", "border": f"1px solid {_BORDER}"}),
    ])


def _contributor_card(
    name: str, role: str, designation: str, dept: str,
    institution: str, bio: str, badges: list,
    icon_color: str = _ACCENT, border_color: str = _ACCENT,
):
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(
                    name[0].upper(),
                    style={
                        "width": "52px", "height": "52px", "borderRadius": "50%",
                        "background": f"linear-gradient(135deg, {icon_color} 0%, {_DARK} 100%)",
                        "color": "white", "fontWeight": "800", "fontSize": "1.35rem",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "flexShrink": "0",
                    }
                ),
            ], width="auto"),
            dbc.Col([
                html.Div(name, style={
                    "fontWeight": "800", "fontSize": "1rem", "color": _DARK,
                    "lineHeight": "1.2", "marginBottom": "0.1rem",
                }),
                html.Div(designation, style={
                    "fontWeight": "600", "fontSize": "0.8rem", "color": icon_color,
                    "marginBottom": "0.05rem",
                }),
                html.Div(dept, style={
                    "fontSize": "0.77rem", "color": _MUTED,
                }),
                html.Div(institution, style={
                    "fontSize": "0.77rem", "color": _MUTED, "fontStyle": "italic",
                }),
            ]),
        ], align="center", className="mb-3"),

        html.Div(html.Em(f'"{role}"'), style={
            "fontSize": "0.8rem", "color": icon_color, "fontWeight": "600",
            "marginBottom": "0.55rem",
        }),

        html.P(bio, style={
            "fontSize": "0.83rem", "color": "#343a40",
            "lineHeight": "1.7", "marginBottom": "0.75rem",
        }),

        html.Div([
            dbc.Badge(b, color="primary", className="me-1 mb-1",
                      style={"fontSize": "0.7rem", "fontWeight": "500"})
            for b in badges
        ]),
    ], style={
        "background": _BG_LIGHT, "borderRadius": "10px",
        "padding": "1.2rem 1.4rem",
        "border": f"1px solid {_BORDER}",
        "borderLeft": f"4px solid {border_color}",
        "height": "100%",
    })
