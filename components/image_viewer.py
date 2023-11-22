import dash_mantine_components as dmc
from dash import dcc, html

from utils.plot_utils import blank_fig

COMPONENT_STYLE = {
    "width": "100vw",
    "height": "100vh",
    "overflowY": "auto",
}

FIGURE_CONFIG = {"displayModeBar": False, "scrollZoom": True, "doubleClick": False}


def layout():
    """
    Returns the layout for the image viewer in the app UI
    """
    return html.Div(
        style=COMPONENT_STYLE,
        children=[
            dcc.Store("image-metadata", data={"name": None}),
            dcc.Store("screen-size"),
            dcc.Location("url"),
            dcc.Graph(
                id="image-viewer",
                config=FIGURE_CONFIG,
                figure=blank_fig(),
                style={
                    "width": "100vw",
                    "height": "100vh",
                    "position": "fixed",
                },
            ),
            dcc.Graph(
                id="image-viewfinder",
                figure=blank_fig(),
                config={"displayModeBar": False},
                style={
                    "position": "absolute",
                    "top": "35px",
                    "right": "15px",
                },
            ),
        ],
    )
