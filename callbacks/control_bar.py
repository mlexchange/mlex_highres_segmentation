from dash import Input, Output, State, callback, Patch, MATCH, ALL, ctx
import dash_mantine_components as dmc
import json
from utils.data_utils import convert_hex_to_rgba
from tifffile import imread
import numpy as np


@callback(
    Output("colormap-scale", "min"),
    Output("colormap-scale", "max"),
    Output("colormap-scale", "value"),
    Input("image-selection-slider", "value"),
    Input("project-data", "data"),
)
def set_color_range(image_idx, project_data):
    if image_idx:
        image_idx -= 1  # slider starts at 1, so subtract 1 to get the correct index

        project_name = project_data["project_name"]
        selected_file = project_data["project_files"][image_idx]
        tf = imread(f"data/{project_name}/{selected_file}")
        min_color = np.min(tf)
        max_color = np.max(tf)
        return min_color, max_color, [min_color, max_color]
    else:
        return 0, 255, [0, 255]


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("annotation-opacity", "value"),
    prevent_initial_call=True,
)
def annotation_opacity(opacity_value):
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["opacity"] = opacity_value
    return patched_figure


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("paintbrush-width", "value"),
    prevent_initial_call=True,
)
def annotation_width(width_value):
    """
    This callback is responsible for changing the brush width.
    """
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["line"]["width"] = width_value
    return patched_figure


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("annotation-class-selection", "className"),
    Input({"type": "annotation-color", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def annotation_color(color_value):
    """
    This callback is responsible for changing the color of the brush.
    """
    color_name = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
    hex_color = dmc.theme.DEFAULT_COLORS[color_name][7]
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = convert_hex_to_rgba(
        hex_color, 0.3
    )
    patched_figure["layout"]["newshape"]["line"]["color"] = hex_color
    return patched_figure, color_name


@callback(
    Output("annotation-store", "data"),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx)

    patched_figure = Patch()
    if checked:
        store["visible"] = True
        patched_figure["layout"]["shapes"] = store[image_idx]
    else:
        annotation_data = (
            [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
        )
        store[image_idx] = annotation_data
        patched_figure["layout"]["shapes"] = []

    return store, patched_figure
