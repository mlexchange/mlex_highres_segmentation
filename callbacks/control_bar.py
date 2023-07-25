from dash import (
    Input,
    Output,
    State,
    callback,
    Patch,
    ALL,
    ctx,
    clientside_callback,
)
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from utils.data_utils import data


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
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def annotation_mode(open, closed, circle, rect, off_mode, annotation_store):
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

    if triggered == "open-freeform" and open > 0:
        patched_figure["layout"]["dragmode"] = "drawopenpath"
        annotation_store["dragmode"] = "drawopenpath"
        open_style = active
    if triggered == "closed-freeform" and closed > 0:
        patched_figure["layout"]["dragmode"] = "drawclosedpath"
        annotation_store["dragmode"] = "drawclosedpath"
        close_style = active
    if triggered == "circle" and circle > 0:
        patched_figure["layout"]["dragmode"] = "drawcircle"
        annotation_store["dragmode"] = "drawcircle"
        circle_style = active
    if triggered == "rectangle" and rect > 0:
        patched_figure["layout"]["dragmode"] = "drawrect"
        annotation_store["dragmode"] = "drawrect"
        rect_style = active
    if triggered == "drawing-off" and off_mode > 0:
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
    Output("bad-label-color", "children"),
    Input("annotation-class-label", "value"),
    Input("annotation-class-colorpicker", "value"),
    State({"type": "annotation-color", "index": ALL}, "children"),
    State({"type": "annotation-color", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def disable_class_creation(label, color, current_labels, current_colors):
    if color is None:
        color = "rgb(255, 255, 255)"
    current_colors = [style["background-color"] for style in current_colors]
    warning_text = []
    if label in current_labels:
        warning_text.append(
            dmc.Text("This annotation class label is already in use.", color="red")
        )
    if color in current_colors:
        warning_text.append(
            dmc.Text("This annotation class color is already in use.", color="red")
        )
    if (
        label is None
        or len(label) == 0
        or label in current_labels
        or color in current_colors
    ):
        return True, warning_text
    else:
        return False, warning_text


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
    State({"type": "annotation-delete-buttons", "index": ALL}, "children"),
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
    class_names,
    annotation_store,
):
    """Updates the list of available annotation classes"""
    triggered = ctx.triggered_id
    current_stored_classes = annotation_store["classes"]
    if triggered == "create-annotation-class":
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
        new_idx = int(max(list(current_stored_classes.keys())))
        current_stored_classes[new_idx + 1] = class_label
        annotation_store["classes"] = current_stored_classes
        return current_classes, "", annotation_store
    else:
        color_to_delete = []
        color_to_keep = []
        for i in range(len(classes_to_delete)):
            if classes_to_delete[i]["border"] == "3px solid black":
                color_to_delete.append(classes_to_delete[i]["background-color"])
                current_stored_classes = {
                    key: val
                    for key, val in current_stored_classes.items()
                    if val != class_names[i]
                }
        for color in current_classes:
            if color["props"]["id"]["index"] not in color_to_delete:
                color_to_keep.append(color)
        annotation_store["classes"] = current_stored_classes
        return color_to_keep, "", annotation_store


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


clientside_callback(
    """
    function eraseShape(_, graph_id) {
        Plotly.eraseActiveShape(graph_id)
        return dash_clientside.no_update
    }
    """,
    Output("image-viewer", "id", allow_duplicate=True),
    Input("eraser", "n_clicks"),
    State("image-viewer", "id"),
    prevent_initial_call=True,
)
