from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from utils.plot_utils import blank_fig

COMPONENT_STYLE = {
    "width": "100vw",
    "height": "100vh",
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
            dcc.Store("image-metadata", data={"name": None}),
            dcc.Store("screen-size"),
            dcc.Location("url"),
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
                        style={
                            "width": "100vw",
                            "height": "100vh",
                            "position": "fixed",
                            "z-index": 1,
                        },
                    ),
                    dcc.Graph(
                        id="image-viewfinder",
                        figure=blank_fig(),
                        config={"displayModeBar": False},
                    ),
                ],
                style={"height": "100vh", "width": "100vw"},
            ),
        ],
    )
