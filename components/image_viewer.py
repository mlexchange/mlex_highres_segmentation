from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from utils.plot_utils import blank_fig


def layout():
    return html.Div(
        style={
            "width": "calc(100vw)",
        },
        children=[
            dmc.Grid(
                id="image-slice-selection-parent",
                style={
                    "z-index": "2",
                    "background-color": "white",
                    "position": "relative",
                },
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
                    dcc.Store(id="image-data"),
                    dcc.Store(id="image-ratio"),
                    dcc.Store(id="image-resized"),
                    dcc.Graph(
                        id="image-viewer",
                        config={
                            "displayModeBar": False,
                            "scrollZoom": True,
                        },
                        figure=blank_fig(),
                        style={
                            "height": "100%",
                            "width": "100vw",
                            "position": "fixed",
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
            ),
        ],
    )
