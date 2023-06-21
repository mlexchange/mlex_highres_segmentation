from dash import Input, Output, State, callback, Patch, MATCH, ALL, ctx
import dash_mantine_components as dmc
import json
from utils.data_utils import convert_hex_to_rgba
import json
from PIL import Image


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
    State("image-slider", "value"),
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
        if annotation_data:
            store[image_idx] = annotation_data
        patched_figure["layout"]["shapes"] = []

    return store, patched_figure


@callback(
    Output("data-management-modal", "opened"),
    Input("open-data-management-modal-button", "n_clicks"),
    State("data-management-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_modal(n_clicks, opened):
    print(not opened)
    return not opened


@callback(
    Output("data-modal-save-status", "children"),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("data-management-modal", "opened"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-slider", "value"),
    prevent_initial_call=True,
)
def save_data(modal_trigger, store, figure, image_idx):
    """
    This callback is responsible for saving the annotation data to the store.
    """
    image_idx = str(image_idx)
    annotation_data = (
        [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
    )
    if annotation_data:
        store[image_idx] = annotation_data

    # TODO: save store to the server file-user system
    return "Data saved!", store


@callback(
    Output("export-annotations", "data"),
    Input("export-annotations-json", "n_clicks"),
    Input("export-annotations-tiff", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def export_annotations(n_clicks_json, n_clicks_tiff, store):
    """
    This callback is responsible for exporting the annotations to a JSON file.
    """
    if ctx.triggered[0]["prop_id"].split(".")[0] == "export-annotations-json":
        data = json.dumps(store)
        filename = "annotations.json"
        mime_type = "application/json"
    else:
        # TODO: export annotations to tiff
        data = json.dumps(store)
        filename = "annotations.tiff"
        mime_type = "image/tiff"

    return dict(content=data, filename=filename, type=mime_type)
