from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from utils.plot_utils import blank_fig

COMPONENT_STYLE = {
    "width": "calc(-440px + 100vw)",
    "height": "calc(100vh - 40px)",
    "padding": "10px",
    "borderRadius": "5px",
    "border": "1px solid rgb(222, 226, 230)",
    "overflowY": "auto",
}

FIGURE_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": True,
}


def layout():
    return html.Div(
        style=COMPONENT_STYLE,
        children=[
            dmc.LoadingOverlay(
                id="image-viewer-loading",
                overlayOpacity=0.15,
                loaderProps=dict(
                    color=dmc.theme.DEFAULT_COLORS["blue"][6], variant="bars"
                ),
                children=[
                    dcc.Graph(
                        id="image-viewer",
                        config=FIGURE_CONFIG,
                        figure=blank_fig(),
                        style={"margin": "auto", "height": "calc(-150px + 100vh)"},
                    ),
                    dcc.Graph(
                        id="image-viewfinder",
                        figure=blank_fig(),
                        config={"displayModeBar": False},
                        style={"width": "10vh", "height": "10vh"},
                    ),
                ],
                style={"display": "flex"},
            ),
        ],
    )
