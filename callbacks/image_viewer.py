from dash import Input, Output, callback
from tifffile import imread
import plotly.express as px
import numpy as np


@callback(Output("image-viewer", "figure"), Input("image-src", "value"))
def render_image(img):
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
    return fig
