import json
import os
import random
import time

import dash_mantine_components as dmc
import plotly.express as px
from dash import (
    ALL,
    MATCH,
    Input,
    Output,
    Patch,
    State,
    callback,
    clientside_callback,
    ctx,
    dcc,
    html,
    no_update,
)
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from components.annotation_class import annotation_class_item
from constants import ANNOT_ICONS, ANNOT_NOTIFICATION_MSGS, KEY_MODES
from utils.annotations import Annotations
from utils.data_utils import (
    DEV_filter_json_data_by_timestamp,
    DEV_load_exported_json_data,
)

# TODO - temporary local file path and user for annotation saving and exporting
EXPORT_FILE_PATH = "data/exported_annotation_data.json"
USER_NAME = "user1"

# Create an empty file if it doesn't exist
if not os.path.exists(EXPORT_FILE_PATH):
    with open(EXPORT_FILE_PATH, "w") as f:
        pass


@callback(
    Output("current-class-selection", "data", allow_duplicate=True),
    Input({"type": "annotation-class", "index": ALL}, "n_clicks"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def update_current_class_selection(class_selected, all_annotation_classes):
    current_selection = None
    if ctx.triggered_id:
        if len(ctx.triggered) == 1:
            for c in all_annotation_classes:
                if c["class_id"] == ctx.triggered_id["index"]:
                    current_selection = c["color"]
        # More than one item in the trigger means the trigger comes from adding/deleting a new class
        # make the selected class the last one in the UI
        elif len(all_annotation_classes) > 0:
            current_selection = all_annotation_classes[-1]["color"]
    return current_selection


@callback(
    Output({"type": "annotation-class", "index": ALL}, "style"),
    Input("current-class-selection", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
)
def update_selected_class_style(selected_class, all_annotation_classes):
    """
    This callback is responsible for updating the style of the selected annotation class to make it appear
    like it has been "selected"
    """
    default_style = {
        "border": "1px solid #EAECEF",
        "borderRadius": "3px",
        "marginBottom": "4px",
        "display": "flex",
        "justifyContent": "space-between",
    }
    selected_style = {
        "border": "1px solid #EAECEF",
        "borderRadius": "3px",
        "marginBottom": "4px",
        "display": "flex",
        "justifyContent": "space-between",
        "backgroundColor": "#EAECEF",
    }
    ids = [c["color"] for c in all_annotation_classes]
    if selected_class in ids:
        # find index of selected class and change its style
        index = ids.index(selected_class)
        styles = [default_style] * len(ids)
        styles[index] = selected_style
        return styles
    else:
        # set last class to selected style
        styles = [default_style] * len(ids)
        styles[-1] = selected_style
        return styles


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("open-freeform", "style"),
    Output("closed-freeform", "style"),
    Output("line", "style"),
    Output("circle", "style"),
    Output("rectangle", "style"),
    Output("eraser", "style"),
    Output("pan-and-zoom", "style"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Input("open-freeform", "n_clicks"),
    Input("closed-freeform", "n_clicks"),
    Input("circle", "n_clicks"),
    Input("rectangle", "n_clicks"),
    Input("line", "n_clicks"),
    Input("eraser", "n_clicks"),
    Input("pan-and-zoom", "n_clicks"),
    Input("keybind-event-listener", "event"),
    State("annotation-store", "data"),
    State("image-viewer-loading", "zIndex"),
    State("generate-annotation-class-modal", "opened"),
    State({"type": "edit-annotation-class-modal", "index": ALL}, "opened"),
    prevent_initial_call=True,
)
def annotation_mode(
    open,
    closed,
    circle,
    rect,
    line,
    erase_annotation,
    pan_and_zoom,
    keybind_event_listener,
    annotation_store,
    figure_overlay_z_index,
    generate_modal_opened,
    edit_modal_opened,
):
    """
    This callback is responsible for changing the annotation mode and the style of the buttons.
    It also accepts keybinds to change the annotation mode.
    """
    if generate_modal_opened or any(edit_modal_opened):
        # user is going to type on this page (on a modal) and we don't want to trigger this callback using keys
        raise PreventUpdate
    # if the image is loading stop the callback when keybinds are pressed
    if figure_overlay_z_index != -1:
        raise PreventUpdate

    trigger = ctx.triggered_id
    pressed_key = (
        keybind_event_listener.get("key", None) if keybind_event_listener else None
    )
    mode = None
    if trigger == "keybind-event-listener":
        if pressed_key in KEY_MODES:
            mode, trigger = KEY_MODES[pressed_key]
        else:
            # if the callback was triggered by pressing a key that is not in the `KEY_MODES`, stop the callback
            raise PreventUpdate

    active = {"backgroundColor": "#EAECEF"}
    inactive = {"border": "1px solid white"}

    patched_figure = Patch()

    # Define a dictionary to store the styles
    styles = {
        "open-freeform": inactive,
        "closed-freeform": inactive,
        "circle": inactive,
        "rectangle": inactive,
        "line": inactive,
        "eraser": inactive,
        "pan-and-zoom": inactive,
    }

    if mode:
        patched_figure["layout"]["dragmode"] = mode
        annotation_store["dragmode"] = mode
        styles[trigger] = active
    else:
        if trigger == "open-freeform" and open > 0:
            patched_figure["layout"]["dragmode"] = "drawopenpath"
            annotation_store["dragmode"] = "drawopenpath"
            styles[trigger] = active
        elif trigger == "closed-freeform" and closed > 0:
            patched_figure["layout"]["dragmode"] = "drawclosedpath"
            annotation_store["dragmode"] = "drawclosedpath"
            styles[trigger] = active
        elif trigger == "line" and line > 0:
            patched_figure["layout"]["dragmode"] = "drawline"
            annotation_store["dragmode"] = "drawline"
            styles[trigger] = active
        elif trigger == "circle" and circle > 0:
            patched_figure["layout"]["dragmode"] = "drawcircle"
            annotation_store["dragmode"] = "drawcircle"
            styles[trigger] = active
        elif trigger == "rectangle" and rect > 0:
            patched_figure["layout"]["dragmode"] = "drawrect"
            annotation_store["dragmode"] = "drawrect"
            styles[trigger] = active
        elif trigger == "eraser" and erase_annotation > 0:
            patched_figure["layout"]["dragmode"] = "eraseshape"
            annotation_store["dragmode"] = "eraseshape"
            styles[trigger] = active
        elif trigger == "pan-and-zoom" and pan_and_zoom > 0:
            patched_figure["layout"]["dragmode"] = "pan"
            annotation_store["dragmode"] = "pan"
            styles[trigger] = active

    notification = dmc.Notification(
        title=ANNOT_NOTIFICATION_MSGS[trigger],
        message="",
        color="indigo",
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        icon=DashIconify(icon=ANNOT_ICONS[trigger], width=40),
        styles={"icon": {"height": "50px", "width": "50px"}},
    )
    return (
        patched_figure,
        styles["open-freeform"],
        styles["closed-freeform"],
        styles["line"],
        styles["circle"],
        styles["rectangle"],
        styles["eraser"],
        styles["pan-and-zoom"],
        annotation_store,
        notification,
    )


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("paintbrush-width", "value"),
    prevent_initial_call=True,
)
def annotation_width(width_value):
    """This callback is responsible for changing the brush width"""
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["line"]["width"] = width_value
    return patched_figure


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("current-class-selection", "data"),
    Input("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_color(
    current_color,
    slider,
):
    """This callback is responsible for changing the color of the brush"""
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = current_color
    patched_figure["layout"]["newshape"]["line"]["color"] = current_color
    return patched_figure


@callback(
    Output("delete-all-warning", "opened"),
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("clear-all", "n_clicks"),
    Input("modal-cancel-delete-button", "n_clicks"),
    Input("modal-continue-delete-button", "n_clicks"),
    State("delete-all-warning", "opened"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def open_warning_modal(
    delete, cancel_delete, continue_delete, opened, all_class_annotations, image_idx
):
    """
    This callback opens and closes the modal that warns you when you're deleting all annotations,
    and deletes all annotations on the current slice if the user confirms deletion.
    """
    if ctx.triggered_id in ["clear-all", "modal-cancel-delete-button"]:
        return not opened, all_class_annotations, no_update
    if ctx.triggered_id == "modal-continue-delete-button":
        image_idx = str(image_idx - 1)
        for a in all_class_annotations:
            # delete annotations from memory
            if image_idx in a["annotations"]:
                del a["annotations"][image_idx]
        # Update fig with patch so it looks like there are no more annotations without re-rerendering the image
        fig = Patch()
        fig["layout"]["shapes"] = []
        return not opened, all_class_annotations, fig
    else:
        return no_update, all_class_annotations, no_update


@callback(
    Output("generate-annotation-class-modal", "opened"),
    Output("create-annotation-class", "disabled"),
    Output("bad-label-color", "children"),
    Output("annotation-class-colorpicker", "value"),
    Input("generate-annotation-class", "n_clicks"),
    Input("create-annotation-class", "n_clicks"),
    Input("annotation-class-label", "value"),
    Input("annotation-class-colorpicker", "value"),
    State("generate-annotation-class-modal", "opened"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def open_annotation_class_modal(
    generate, create, new_label, new_color, opened, all_annotation_class_store
):
    """
    This callback opens and closes the modal that is used to create a new annotation class and checks
    if color and class name chosen are available
    """
    current_classes = [a["label"] for a in all_annotation_class_store]
    current_colors = [a["color"] for a in all_annotation_class_store]
    if ctx.triggered_id in ["annotation-class-label", "annotation-class-colorpicker"]:
        disable_class_creation = False
        error_msg = []
        if new_label in current_classes:
            disable_class_creation = True
            error_msg.append("Label Already in Use!")
            error_msg.append(html.Br())
        if new_color in current_colors:
            disable_class_creation = True
            error_msg.append("Color Already in use!")
        return no_update, disable_class_creation, error_msg, no_update
    # define 48 sample colors - keep the ones that don't already exist - suggest a random one for the color picker
    color_suggestions = px.colors.qualitative.Dark24 + px.colors.qualitative.Alphabet
    color_suggestions = [c for c in color_suggestions if c not in current_colors]
    random_color = random.choice(color_suggestions) if color_suggestions else "#DB0606"
    return not opened, False, "", random_color


@callback(
    Output({"type": "edit-annotation-class-modal", "index": MATCH}, "opened"),
    Output({"type": "save-edited-annotation-class-btn", "index": MATCH}, "disabled"),
    Output({"type": "bad-edit-label", "index": MATCH}, "children"),
    Output({"type": "edit-annotation-class-modal", "index": MATCH}, "title"),
    Output(
        {"type": "edit-annotation-class-text-input", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"type": "edit-annotation-class-colorpicker", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "edit-annotation-class", "index": MATCH}, "n_clicks"),
    Input({"type": "save-edited-annotation-class-btn", "index": MATCH}, "n_clicks"),
    Input({"type": "edit-annotation-class-text-input", "index": MATCH}, "value"),
    Input({"type": "edit-annotation-class-colorpicker", "index": MATCH}, "value"),
    State({"type": "edit-annotation-class-modal", "index": MATCH}, "opened"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def open_edit_class_modal(
    edit_button,
    edit_modal,
    new_label,
    new_color,
    opened,
    class_to_edit,
    all_annotation_class_store,
):
    """
    This callback opens and closes the modal that allows you to relabel an existing
    annotation class and change its color and checks if the new class name/class color is available.
    """
    modal_title = f"Edit class: {class_to_edit['label']}"
    # add the current class name and color in the modal (in case user wants to only edit one thing)
    if ctx.triggered_id["type"] == "edit-annotation-class":
        return (
            not opened,
            no_update,
            no_update,
            no_update,
            class_to_edit["label"],
            class_to_edit["color"],
        )
    # check for duplicate color/duplicate label
    if ctx.triggered_id["type"] in [
        "edit-annotation-class-text-input",
        "edit-annotation-class-colorpicker",
    ]:
        # get all colors and labels
        current_classes = [a["label"] for a in all_annotation_class_store]
        current_colors = [a["color"] for a in all_annotation_class_store]
        # its ok to rename the current class color/label to its own name
        current_classes.remove(class_to_edit["label"])
        current_colors.remove(class_to_edit["color"])
        edit_disabled = False
        error_msg = []
        if new_label in current_classes:
            error_msg.append("Label Already in Use!")
            error_msg.append(html.Br())
            edit_disabled = True
        if new_color in current_colors:
            error_msg.append("Color Already in use!")
            edit_disabled = True
        return no_update, edit_disabled, error_msg, modal_title, no_update, no_update
    return not opened, False, no_update, modal_title, no_update, no_update


@callback(
    Output({"type": "delete-annotation-class-modal", "index": MATCH}, "opened"),
    Output({"type": "delete-annotation-class-modal", "index": MATCH}, "title"),
    Input({"type": "delete-annotation-class", "index": MATCH}, "n_clicks"),
    Input({"type": "modal-continue-delete-class-btn", "index": MATCH}, "n_clicks"),
    Input({"type": "modal-cancel-delete-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "delete-annotation-class-modal", "index": MATCH}, "opened"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def open_delete_class_modal(
    remove_class,
    continue_remove_class_modal,
    cancel_remove_class_modal,
    opened,
    class_to_delete,
):
    """
    This callback opens and closes the modal that allows you to relabel an existing annotation class
    and triggers the delete_annotation_class() callback.
    """
    modal_title = f"Delete class: {class_to_delete['label']}"
    return not opened, modal_title


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input({"type": "edit-class-store", "index": ALL}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def re_draw_annotations_after_editing_class_color(
    hide_show_click, all_annotation_class_store, image_idx
):
    """
    After editing a class color, the color is changed in the class-store, but the color change is not reflected
    on the image, so we must regenerate the annotations using Patch() so they show up in the right color.
    """
    fig = Patch()
    image_idx = str(image_idx - 1)
    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"] and "annotations" in a and image_idx in a["annotations"]:
            all_annotations += a["annotations"][image_idx]
    fig["layout"]["shapes"] = all_annotations
    return fig


@callback(
    Output({"type": "annotation-class-label", "index": MATCH}, "children"),
    Output({"type": "annotation-class-color", "index": MATCH}, "style"),
    Output({"type": "annotation-class-store", "index": MATCH}, "data"),
    Output({"type": "annotation-class", "index": MATCH}, "n_clicks"),
    Output({"type": "edit-class-store", "index": MATCH}, "data"),
    Input({"type": "save-edited-annotation-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "edit-annotation-class-text-input", "index": MATCH}, "value"),
    State({"type": "edit-annotation-class-colorpicker", "index": MATCH}, "value"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def edit_annotation_class(
    edit_clicked, new_label, new_color, annotation_class_store, img_idx
):
    """
    This callback edits the name and color of an annotation class by updating class-store metadata. We also trigger
    edit-class-store so we can then redraw the annotations in re_draw_annotations_after_editing_class_color().
    """
    img_idx = str(img_idx - 1)
    # update store meta data
    annotation_class_store["label"] = new_label
    annotation_class_store["color"] = new_color
    class_color_identifier = {
        "width": "25px",
        "height": "25px",
        "background-color": new_color + "50",
        "margin": "5px",
        "borderRadius": "3px",
        "border": f"2px solid {new_color}",
    }
    # update color in previous annotation data
    if img_idx in annotation_class_store["annotations"]:
        for a in annotation_class_store["annotations"][img_idx]:
            a["line"]["color"] = new_color
            if "fillcolor" in a:
                a["fillcolor"] = new_color

    return new_label, class_color_identifier, annotation_class_store, 1, True


@callback(
    Output("annotation-class-label", "value"),
    Output("annotation-class-container", "children", allow_duplicate=True),
    Output("current-class-selection", "data"),
    Input("create-annotation-class", "n_clicks"),
    State("annotation-class-container", "children"),
    State("annotation-class-label", "value"),
    State("annotation-class-colorpicker", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def add_annotation_class(
    create, current_classes, new_class_label, new_class_color, all_annotations_data
):
    """This callback adds a new annotation class with the same chosen color and label"""
    existing_ids = [annotation["class_id"] for annotation in all_annotations_data]
    current_classes.append(
        annotation_class_item(new_class_color, new_class_label, existing_ids)
    )
    return "", current_classes, new_class_color


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input({"type": "hide-show-class-store", "index": ALL}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def hide_show_annotations_on_fig(
    hide_show_click, all_annotation_class_store, image_idx
):
    """This callback hides or shows all annotations for a given class by Patching the figure accordingly"""
    fig = Patch()
    image_idx = str(image_idx - 1)
    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"] and "annotations" in a and image_idx in a["annotations"]:
            all_annotations += a["annotations"][image_idx]
    fig["layout"]["shapes"] = all_annotations
    return fig


@callback(
    Output(
        {"type": "annotation-class-store", "index": MATCH}, "data", allow_duplicate=True
    ),
    Output({"type": "hide-show-class-store", "index": MATCH}, "data"),
    Output({"type": "hide-annotation-class", "index": MATCH}, "children"),
    Input({"type": "hide-annotation-class", "index": MATCH}, "n_clicks"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    State({"type": "hide-show-class-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def hide_show_annotation_class(
    hide_show_click,
    annotation_class_store,
    hide_show_class_store,
):
    """
    This callback updates both the annotation-class-store (which contains the annotation data)
    and the hide-show-class-store which is only used to trigger the callback that will
    actually patch the figure: hide_show_annotations_on_fig().
    Also updates the hide/show icon accordingly.
    """
    is_visible = annotation_class_store["is_visible"]
    annotation_class_store["is_visible"] = not is_visible
    hide_show_class_store["is_visible"] = not is_visible
    if is_visible:
        updated_icon = DashIconify(icon="mdi:hide")
    else:
        updated_icon = DashIconify(icon="mdi:eye")
    return annotation_class_store, hide_show_class_store, updated_icon


@callback(
    Output("annotation-class-container", "children"),
    Input({"type": "deleted-class-store", "index": ALL}, "data"),
    State("annotation-class-container", "children"),
    prevent_initial_call=True,
)
def delete_annotation_class(is_deleted, all_classes):
    """This callback deletes the class from memory using the color from the deleted-class-store"""
    is_deleted = [x for x in is_deleted if x is not None]
    if is_deleted:
        is_deleted = is_deleted[0]
        updated_classes = [
            c for c in all_classes if c["props"]["id"]["index"] != is_deleted
        ]
        return updated_classes
    return no_update


@callback(
    Output({"type": "deleted-class-store", "index": MATCH}, "data"),
    Input({"type": "modal-continue-delete-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def clear_annotation_class(
    remove,
    annotation_class_store,
):
    """This callback updates the deleted-class-store with the id of the class to delete"""
    deleted_class = annotation_class_store["class_id"]
    return deleted_class


clientside_callback(
    """
    function dash_filters_clientside(brightness, contrast) {
    console.log(brightness, contrast)
        js_path = "#image-viewer > div.js-plotly-plot > div > div > svg:nth-child(1)"
        changeFilters(js_path, brightness, contrast)
        return ""
    }
    """,
    Output("dummy-output", "children", allow_duplicate=True),
    Input({"type": "slider", "index": "brightness"}, "value"),
    Input({"type": "slider", "index": "contrast"}, "value"),
    prevent_initial_call=True,
)


@callback(
    Output({"type": "slider", "index": MATCH}, "value", allow_duplicate=True),
    Input({"type": "reset", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(n_clicks):
    return 100


# TODO: check this when plotly is updated
clientside_callback(
    """
    function deleteShape(_, graph_id) {
        var gd = document.getElementsByClassName('js-plotly-plot')[0];
        Plotly.deleteActiveShape(gd)
        return dash_clientside.no_update
    }
    """,
    Output("image-viewer", "id", allow_duplicate=True),
    Input("eraser", "n_clicks"),
    State("image-viewer", "id"),
    prevent_initial_call=True,
)


@callback(
    Output("notifications-container", "children"),
    Output("export-annotation-metadata", "data"),
    Output("export-annotation-mask", "data"),
    Input("export-annotation", "n_clicks"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def export_annotation(n_clicks, all_annotations, global_store):
    annotations = Annotations(all_annotations, global_store)
    EXPORT_AS_SPARSE = False  # todo replace with input

    if annotations.has_annotations():
        metadata_file = {
            "content": json.dumps(annotations.get_annotations()),
            "filename": "annotation_metadata.json",
            "type": "application/json",
        }

        annotations.create_annotation_mask(sparse=EXPORT_AS_SPARSE)
        mask_data = annotations.get_annotation_mask_as_bytes()
        mask_file = dcc.send_bytes(mask_data, filename="annotation_masks.zip")

        notification_title = "Annotation Exported!"
        notification_message = "Succesfully exported in .json format."
        notification_color = "green"
    else:
        metadata_file, mask_file = no_update, no_update
        notification_title = "No Annotations to Export!"
        notification_message = "Please annotate an image before exporting."
        notification_color = "red"

    notification = dmc.Notification(
        title=notification_title,
        message=notification_message,
        color=notification_color,
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        icon=DashIconify(icon="entypo:export"),
    )
    return notification, metadata_file, mask_file


@callback(
    Output("data-modal-save-status", "children"),
    Input("save-annotations", "n_clicks"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def save_data(n_clicks, global_store, all_annotations, image_src):
    """This callback is responsible for saving the annotation data to the store"""
    if not n_clicks:
        raise PreventUpdate

    if all_annotations:
        # TODO: save store to the server file-user system, this will be changed to DB later
        export_data = {
            "user": USER_NAME,
            "source": image_src,
            "time": time.strftime("%Y-%m-%d-%H:%M:%S"),
            "data": json.dumps(all_annotations),
        }
        # Convert export_data to JSON string
        export_data_json = json.dumps(export_data)

        # Append export_data JSON string to the file
        if export_data["data"] != "{}":
            with open(EXPORT_FILE_PATH, "a+") as f:
                f.write(export_data_json + "\n")
        return "Data saved!"
    return "No annotations to save!"


@callback(
    Output("data-management-modal", "opened"),
    Output("data-modal-save-status", "children", allow_duplicate=True),
    Input("open-data-management-modal-button", "n_clicks"),
    State("data-management-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_save_load_modal(n_clicks, opened):
    return not opened, ""


@callback(
    Output("load-annotations-server-container", "children"),
    Input("open-data-management-modal-button", "n_clicks"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def populate_load_annotations_dropdown_menu_options(modal_opened, image_src):
    """
    This callback populates dropdown window with all saved annotation options for the given project name.
    It then creates buttons with info about the save, which when clicked, loads the data from the server.
    """
    if not modal_opened:
        raise PreventUpdate

    data = DEV_load_exported_json_data(EXPORT_FILE_PATH, USER_NAME, image_src)
    if not data:
        return "No annotations found for the selected data source."

    buttons = []
    for item in data:
        annotations = item["data"]
        num_classes = len(annotations)
        buttons.append(
            dmc.Button(
                f"{num_classes} classes, created at {item['time']}",
                id={"type": "load-server-annotations", "index": item["time"]},
                variant="light",
            )
        )

    return dmc.Stack(
        buttons,
        spacing="xs",
        style={"overflow": "auto", "max-height": "300px"},
    )


@callback(
    Output("annotation-class-container", "children", allow_duplicate=True),
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

    annotations = []
    for annotation_class in data:
        annotations.append(annotation_class_item(None, None, None, annotation_class))

    return annotations, False


@callback(
    Output("drawer-controls", "opened"),
    Output("drawer-controls-open-button", "style"),
    Input("drawer-controls-open-button", "n_clicks"),
    Input("drawer-controls", "opened"),
)
def open_controls_drawer(n_clicks, is_opened):
    if ctx.triggered_id == "drawer-controls-open-button":
        return True, no_update
    if ctx.triggered_id == "drawer-controls":
        if is_opened:
            return no_update, {"display": "none"}
        return no_update, {}
    return no_update, no_update
