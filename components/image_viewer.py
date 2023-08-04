from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from utils.plot_utils import blank_fig

COMPONENT_STYLE = {
    "width": "calc(100vw)",
    "height": "calc(100vh - 40px)",
    "padding": "10px",
    "borderRadius": "5px",
    "border": "1px solid rgb(222, 226, 230)",
    "overflowY": "auto",
}

FIGURE_CONFIG = {
    "modeBarButtonsToAdd": [
        "drawopenpath",
        "drawclosedpath",
        "eraseshape",
        "drawline",
        "drawcircle",
        "drawrect",
    ],
    "scrollZoom": True,
    "modeBarButtonsToRemove": [
        "zoom",
        "zoomin",
        "zoomout",
        "autoscale",
    ],
}


def layout():
    return html.Div(
        style=COMPONENT_STYLE,
        children=[
            dmc.Grid(
                id="image-slice-selection-parent",
                children=[
                    dmc.Col(
                        dmc.Tooltip(
                            label="Previous image",
                            children=dmc.ActionIcon(
                                DashIconify(icon="ooui:previous-ltr", width=20),
                                variant="filled",
                                id="image-selection-previous",
                                mt=15,
                            ),
                        ),
                        span=1,
                        offset=0.5,
                    ),
                    dmc.Col(
                        [
                            dmc.Text(
                                "Selected image: 1",
                                align="center",
                                id="image-selection-text",
                            ),
                            dmc.Slider(
                                min=1,
                                max=1000,
                                step=1,
                                value=25,
                                id="image-selection-slider",
                            ),
                        ],
                        span="auto",
                    ),
                    dmc.Col(
                        dmc.Tooltip(
                            label="Next image",
                            children=dmc.ActionIcon(
                                DashIconify(icon="ooui:previous-rtl", width=20),
                                variant="filled",
                                id="image-selection-next",
                                mt=15,
                            ),
                        ),
                        span=1,
                    ),
                ],
            ),
            dmc.Space(h=20),
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
                            "height": "90vh",
                            "width": "90vw",
                            "position": "fixed",
                            "top": "12vh",
                            "left": "0",
                        },
                    ),
                    dcc.Graph(
                        id="image-viewfinder",
                        figure=blank_fig(),
                        config={"displayModeBar": False},
                        style={
                            "width": "10vh",
                            "height": "10vh",
                            "position": "absolute",
                            "top": "30px",
                            "right": "10px",
                        },
                    ),
                ],
                style={
                    "height": "100%",
                    "width": "90vw",
                },
            ),
        ],
    )
