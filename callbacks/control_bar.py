from dash import Input, Output, State, callback, Patch, MATCH, ALL, ctx
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate
import json
from utils.data_utils import (
    convert_hex_to_rgba,
    DEV_load_exported_json_data,
    DEV_filter_json_data_by_timestamp,
)
import json
import os
import time

EXPORT_FILE_PATH = "data/exported_annotation_data.json"
USER_NAME = "user1"

# Create an empty file if it doesn't exist
if not os.path.exists(EXPORT_FILE_PATH):
    with open(EXPORT_FILE_PATH, "w") as f:
        pass
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
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, annotation_store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx)

    patched_figure = Patch()
    if checked:
        annotation_store["visible"] = True
        patched_figure["layout"]["shapes"] = annotation_store[image_idx]
    else:
        annotation_data = (
            [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
        )
        if annotation_data:
            annotation_store[image_idx] = annotation_data
        patched_figure["layout"]["shapes"] = []

    return annotation_store, patched_figure


@callback(
    Output("data-management-modal", "opened"),
    Output("data-modal-save-status", "children", allow_duplicate=True),
    Input("open-data-management-modal-button", "n_clicks"),
    State("data-management-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_modal(n_clicks, opened):
    return not opened, ""


@callback(
    Output("data-modal-save-status", "children"),
    # Output("annotation-store", "data", allow_duplicate=True),
    Input("save-annotations", "n_clicks"),
    State("annotation-store", "data"),
    # State("image-viewer", "figure"),
    # State("image-selection-slider", "value"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def save_data(n_clicks, annotation_store, image_src):
    """
    This callback is responsible for saving the annotation data to the store.
    """
    if not n_clicks:
        raise PreventUpdate
    # annotation_data = (
    #     [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
    # )
    # if annotation_data:
    # store[str(image_idx)] = annotation_data

    # TODO: save store to the server file-user system, this will be changed to DB later
    export_data = {
        "user": USER_NAME,
        "source": image_src,
        "time": time.strftime("%Y-%m-%d-%H:%M:%S"),
        "data": json.dumps(annotation_store),
    }
    # Convert export_data to JSON string
    export_data_json = json.dumps(export_data)

    # Append export_data JSON string to the file
    if export_data["data"] != "{}":
        with open(EXPORT_FILE_PATH, "a+") as f:
            f.write(export_data_json + "\n")
    return "Data saved!"


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


@callback(
    Output("load-annotations-server-container", "children"),
    Input("open-data-management-modal-button", "n_clicks"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def populate_load_server_annotations(modal_opened, image_src):
    """
    This callback is responsible for saving the annotation data the storage, and also creting a layout for selecting saved annotations so they are loaded.
    """
    if not modal_opened:
        raise PreventUpdate

    # TODO : when quering from the server, get (annotation save time) for user, source, order by time
    data = DEV_load_exported_json_data(EXPORT_FILE_PATH, USER_NAME, image_src)
    if not data:
        return "No annotations found for the selected data source."
    # TODO : when quering from the server, load data for user, source, order by time

    buttons = [
        dmc.Button(
            f"{data_json['time']}",
            id={"type": "load-server-annotations", "index": data_json["time"]},
            variant="light",
        )
        for i, data_json in enumerate(data)
    ]

    return dmc.Stack(
        buttons,
        spacing="xs",
        style={"overflow": "auto", "max-height": "300px"},
    )


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("data-management-modal", "opened", allow_duplicate=True),
    Input({"type": "load-server-annotations", "index": ALL}, "n_clicks"),
    State("project-name-src", "value"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def load_and_apply_selected_annotations(selected_annotation, image_src, img_idx):
    """
    This callback is responsible for loading and applying the selected annotations when user selects them from the modal.
    """
    # this callback is triggered when the buttons are created, when that happens we can stop it
    if all([x is None for x in selected_annotation]):
        raise PreventUpdate

    selected_annotation_timestamp = json.loads(
        ctx.triggered[0]["prop_id"].split(".")[0]
    )["index"]

    # TODO : when quering from the server, load (data) for user, source, time
    data = DEV_load_exported_json_data(EXPORT_FILE_PATH, USER_NAME, image_src)
    data = DEV_filter_json_data_by_timestamp(data, str(selected_annotation_timestamp))
    data = data[0]["data"]
    # TODO : when quering from the server, load (data) for user, source, time
    print(data)
    patched_figure = Patch()
    patched_figure["layout"]["shapes"] = data[str(img_idx)]
    return patched_figure, data, False
