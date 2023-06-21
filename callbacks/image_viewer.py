from dash import Input, Output, State, callback
import dash_mantine_components as dmc
from tifffile import imread
import plotly.express as px
import numpy as np
from utils.data_utils import convert_hex_to_rgba


@callback(
    Output("image-viewer", "figure"),
    Input("image-src", "value"),
    State("paintbrush-width", "value"),
    State("annotation-opacity", "value"),
    State("annotation-class-selection", "className"),
)
def render_image(img, annotation_width, annotation_opacity, annotation_color):
    if img:
        tf = imread(f"data/{img}")
    else:
        tf = np.zeros((500, 500))
    fig = px.imshow(tf, binary_string=True)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        dragmode="pan",
        height=620,
        width=620,
    )

    # set the default annotation style
    hex_color = dmc.theme.DEFAULT_COLORS[annotation_color][7]
    fig.update_layout(
        newshape=dict(
            line=dict(color=annotation_color, width=annotation_width),
            fillcolor=convert_hex_to_rgba(hex_color, 0.3),
            opacity=annotation_opacity,
        )
    )
    return fig
