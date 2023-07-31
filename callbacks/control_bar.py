from dash import (
    Input,
    Output,
    dcc,
    State,
    callback,
    Patch,
    ALL,
    ctx,
    clientside_callback,
    no_update,
)
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import json
from utils.annotations import Annotations
import random


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("open-freeform", "style"),
    Output("closed-freeform", "style"),
    Output("circle", "style"),
    Output("rectangle", "style"),
    Output("drawing-off", "style"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("current-ann-mode", "data", allow_duplicate=True),
    Input("open-freeform", "n_clicks"),
    Input("closed-freeform", "n_clicks"),
    Input("circle", "n_clicks"),
    Input("rectangle", "n_clicks"),
    Input("drawing-off", "n_clicks"),
    Input("keybind-event-listener", "event"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def annotation_mode(
    open, closed, circle, rect, off_mode, keybind_event_listener, annotation_store
):
    """This callback determines which drawing mode the graph is in"""
    if not annotation_store["visible"]:
        raise PreventUpdate

    patched_figure = Patch()
    triggered = ctx.triggered_id
    active = {"border": "3px solid black"}
    inactive = {"border": "1px solid"}
    open_style = inactive
    close_style = inactive
    circle_style = inactive
    rect_style = inactive
    pan_style = inactive

    (
        key_open_freeform,
        key_closed_freeform,
        key_circle,
        key_rectangle,
        key_drawing_off,
    ) = (
        False,
        False,
        False,
        False,
        False,
    )
    if triggered == "keybind-event-listener":
        pressed_key = keybind_event_listener["key"]
        if pressed_key == "1":
            key_open_freeform = True
        elif pressed_key == "2":
            key_closed_freeform = True
        elif pressed_key == "3":
            key_circle = True
        elif pressed_key == "4":
            key_rectangle = True
        elif pressed_key == "5":
            key_drawing_off = True

    if key_open_freeform or (triggered == "open-freeform" and open > 0):
        patched_figure["layout"]["dragmode"] = "drawopenpath"
        annotation_store["dragmode"] = "drawopenpath"
        open_style = active
    if key_closed_freeform or (triggered == "closed-freeform" and closed > 0):
        patched_figure["layout"]["dragmode"] = "drawclosedpath"
        annotation_store["dragmode"] = "drawclosedpath"
        close_style = active
    if key_circle or (triggered == "circle" and circle > 0):
        patched_figure["layout"]["dragmode"] = "drawcircle"
        annotation_store["dragmode"] = "drawcircle"
        circle_style = active
    if key_rectangle or (triggered == "rectangle" and rect > 0):
        patched_figure["layout"]["dragmode"] = "drawrect"
        annotation_store["dragmode"] = "drawrect"
        rect_style = active
    if key_drawing_off or (triggered == "drawing-off" and off_mode > 0):
        patched_figure["layout"]["dragmode"] = "pan"
        annotation_store["dragmode"] = "pan"
        pan_style = active
    return (
        patched_figure,
        open_style,
        close_style,
        circle_style,
        rect_style,
        pan_style,
        annotation_store,
        triggered,
    )


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
    Output("current-annotation-classes", "children"),
    Input("annotation-class-selection", "children"),
    prevent_initial_call=True,
)
def make_class_delete_modal(current_classes):
    """Creates buttons for the delete selected classes modal"""
    for button in current_classes:
        color = button["props"]["style"]["background-color"]
        button["props"]["id"] = {"type": "annotation-delete-buttons", "index": color}
        button["props"]["style"]["border"] = "1px solid"
    return current_classes


@callback(
    Output({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    Input({"type": "annotation-delete-buttons", "index": ALL}, "n_clicks"),
    State({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def highlight_selected_classes(selected_classes, current_styles):
    for i in range(len(selected_classes)):
        if selected_classes[i] is not None and selected_classes[i] % 2 != 0:
            current_styles[i]["border"] = "3px solid black"
        else:
            current_styles[i]["border"] = "1px solid"
    return current_styles


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output({"type": "annotation-color", "index": ALL}, "style"),
    Input({"type": "annotation-color", "index": ALL}, "n_clicks"),
    State({"type": "annotation-color", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def annotation_color(color_value, current_style):
    """
    This callback is responsible for changing the color of the brush.
    """
    color = ctx.triggered_id["index"]
    for i in range(len(current_style)):
        if current_style[i]["background-color"] == color:
            current_style[i]["border"] = "3px solid black"
        else:
            current_style[i]["border"] = "1px solid"
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = color
    patched_figure["layout"]["newshape"]["line"]["color"] = color
    return patched_figure, current_style


@callback(
    Output("delete-all-warning", "opened"),
    Input("delete-all", "n_clicks"),
    Input("modal-cancel-button", "n_clicks"),
    Input("modal-delete-button", "n_clicks"),
    State("delete-all-warning", "opened"),
    prevent_initial_call=True,
)
def open_warning_modal(delete, cancel, delete_4_real, opened):
    return not opened


@callback(
    Output("generate-annotation-class-modal", "opened"),
    Input("generate-annotation-class", "n_clicks"),
    Input("create-annotation-class", "n_clicks"),
    State("generate-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_annotation_class_modal(generate, create, opened):
    return not opened


@callback(
    Output("delete-annotation-class-modal", "opened"),
    Input("delete-annotation-class", "n_clicks"),
    Input("remove-annotation-class", "n_clicks"),
    State("delete-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_delete_class_modal(delete, remove, opened):
    return not opened


@callback(
    Output("create-annotation-class", "disabled"),
    Input("annotation-class-label", "value"),
)
def disable_class_creation(label):
    if label is None or len(label) == 0:
        return True
    else:
        return False


@callback(
    Output("remove-annotation-class", "disabled"),
    Output("at-least-one", "style"),
    Input({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def disable_class_deletion(highlighted):
    num_selected = 0
    for style in highlighted:
        if style["border"] == "3px solid black":
            num_selected += 1
    if num_selected == 0:
        return True, {"display": "none"}
    if num_selected == len(highlighted):
        return True, {"display": "initial"}
    else:
        return False, {"display": "none"}


@callback(
    Output("annotation-class-selection", "children"),
    Output("annotation-class-label", "value"),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("create-annotation-class", "n_clicks"),
    Input("remove-annotation-class", "n_clicks"),
    State("annotation-class-label", "value"),
    State("annotation-class-colorpicker", "value"),
    State("annotation-class-selection", "children"),
    State({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def add_new_class(
    create,
    remove,
    class_label,
    class_color,
    current_classes,
    classes_to_delete,
    annotation_store,
):
    """Updates the list of available annotation classes"""
    triggered = ctx.triggered_id
    if triggered == "create-annotation-class":
        # TODO: Check that the randint isn't already assigned to a class
        annotation_store["label_mapping"].append(
            {"color": class_color, "id": random.randint(1, 100), "label": class_label}
        )
        if class_color is None:
            class_color = "rgb(255, 255, 255)"
        if class_color == "rgb(255, 255, 255)":
            current_classes.append(
                dmc.ActionIcon(
                    id={"type": "annotation-color", "index": class_color},
                    w=30,
                    variant="filled",
                    style={
                        "background-color": class_color,
                        "border": "1px solid",
                        "color": "black",
                    },
                    children=class_label,
                )
            )
        else:
            current_classes.append(
                dmc.ActionIcon(
                    id={"type": "annotation-color", "index": class_color},
                    w=30,
                    variant="filled",
                    style={"background-color": class_color, "border": "1px solid"},
                    children=class_label,
                )
            )
        output_classes = current_classes
    else:
        # TODO: Remove mapping from the store
        color_to_delete = []
        color_to_keep = []
        for color_opt in classes_to_delete:
            if color_opt["border"] == "3px solid black":
                color_to_delete.append(color_opt["background-color"])
        for color in current_classes:
            if color["props"]["id"]["index"] not in color_to_delete:
                color_to_keep.append(color)
        output_classes = color_to_keep

    return output_classes, "", annotation_store


@callback(
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    Input("modal-delete-button", "n_clicks"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, delete_all, annotation_store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx - 1)
    patched_figure = Patch()
    if ctx.triggered_id == "modal-delete-button":
        annotation_store["annotations"][image_idx] = []
        patched_figure["layout"]["shapes"] = []
    else:
        if checked:
            annotation_store["visible"] = True
            patched_figure["layout"]["visible"] = True
            if str(image_idx) in annotation_store["annotations"]:
                patched_figure["layout"]["shapes"] = annotation_store["annotations"][
                    image_idx
                ]
            patched_figure["layout"]["dragmode"] = annotation_store["dragmode"]
        else:
            new_annotation_data = (
                [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
            )
            annotation_store["visible"] = False
            patched_figure["layout"]["dragmode"] = False
            annotation_store["annotations"][image_idx] = new_annotation_data
            patched_figure["layout"]["shapes"] = []

    return annotation_store, patched_figure


clientside_callback(
    """
    function dash_filters_clientside(brightness, contrast) {
    console.log(brightness, contrast)
        js_path = "#image-viewer > div.js-plotly-plot > div > div > svg:nth-child(1) > g.cartesianlayer > g > g.plot > g"
        changeFilters(js_path, brightness, contrast)
        return ""
    }
    """,
    Output("dummy-output", "children", allow_duplicate=True),
    Input("figure-brightness", "value"),
    Input("figure-contrast", "value"),
    prevent_initial_call=True,
)


@callback(
    Output("figure-brightness", "value", allow_duplicate=True),
    Output("figure-contrast", "value", allow_duplicate=True),
    Input("filters-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(n_clicks):
    default_brightness = 100
    default_contrast = 100
    return default_brightness, default_contrast


@callback(
    Output("notifications-container", "children"),
    Output("export-annotation-metadata", "data"),
    Output("export-annotation-mask", "data"),
    Input("export-annotation", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def export_annotation(n_clicks, annotation_store):
    EXPORT_AS_SPARSE = False  # todo replace with input
    if not annotation_store["annotations"]:
        metadata_data = no_update
        notification_title = "No Annotations to Export!"
        notification_message = "Please annotate an image before exporting."
        notification_color = "red"
    else:
        annotations = Annotations(annotation_store)

        # medatada
        annotations.create_annotation_metadata()
        metadata_file = {
            "content": json.dumps(annotations.get_annotations()),
            "filename": "annotation_metadata.json",
            "type": "application/json",
        }

        # mask data
        annotations.create_annotation_mask(sparse=EXPORT_AS_SPARSE)
        mask_data = annotations.get_annotation_mask_as_bytes()
        mask_file = dcc.send_bytes(mask_data, filename=f"annotation_masks.zip")

        # notification
        notification_title = "Annotation Exported!"
        notification_message = "Succesfully exported in .json format."
        notification_color = "green"

    notification = dmc.Notification(
        title=notification_title,
        message=notification_message,
        color=notification_color,
        id="export-annotation-notification",
        action="show",
        icon=DashIconify(icon="entypo:export"),
    )
    return notification, metadata_file, mask_file
