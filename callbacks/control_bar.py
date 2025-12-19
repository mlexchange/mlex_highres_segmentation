import json
import logging
import os
import random
import time
import uuid
from urllib.parse import urlparse

import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
from dash import (
    ALL,
    MATCH,
    ClientsideFunction,
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
from PIL import Image

from components.annotation_class import annotation_class_item
from components.parameter_items import ParameterItems
from constants import ANNOT_ICONS, ANNOT_NOTIFICATION_MSGS, KEY_MODES, KEYBINDS
from utils.annotations import Annotations
from utils.data_utils import models, tiled_datasets, tiled_masks
from utils.plot_utils import generate_notification, generate_notification_bg_icon_col
from utils.sam3_utils import segment_all_classes_to_polygons  # NEW function
from utils.sam3_utils import (
    convert_sam3_masks_to_numpy,
    extract_rectangles_by_class,
    load_and_prepare_image,
    sam3_segmenter,
)

# Configure logger
logger = logging.getLogger("seg.control_bar")

# TODO - temporary local file path and user for annotation saving and exporting
EXPORT_FILE_PATH = os.getenv("EXPORT_FILE_PATH", "exported_annotation_data.json")
USER_NAME = os.getenv("USER_NAME", "user1")

# Create an empty file if it doesn't exist
if not os.path.exists(EXPORT_FILE_PATH):
    open(EXPORT_FILE_PATH, "w").close()


@callback(
    Output("image-uri", "value"),
    Input("tiled-image-selector", "selectedLinks"),
    prevent_initial_call=True,
)
def update_selected_image_uri(selected_links):
    logger.info(f"Selected image links: {selected_links}")

    if selected_links:
        # Extract the 'self' key from the dictionary
        if isinstance(selected_links, dict) and "self" in selected_links:
            # Extract the full URI from the selected links
            full_uri = selected_links.get("self", "")

            # Parse the URI and extract the path
            parsed_uri = urlparse(full_uri)
            extracted_path = parsed_uri.path

            # Remove the common prefix from the path
            base_data_path = urlparse(tiled_datasets.data_tiled_uri).path
            if extracted_path.startswith(base_data_path):
                extracted_path = extracted_path[len(base_data_path) :]

            # Clean up the extracted path and return
            return extracted_path.strip("/")
        # Fall back to string representation if we can't extract 'self'
        return str(selected_links)
    return ""


@callback(
    Output("current-class-selection", "data", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Input({"type": "annotation-class", "index": ALL}, "n_clicks"),
    Input("keybind-event-listener", "event"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("generate-annotation-class-modal", "opened"),
    State({"type": "edit-annotation-class-modal", "index": ALL}, "opened"),
    State("current-class-selection", "data"),
    State("control-accordion", "value"),
    prevent_initial_call=True,
)
def update_current_class_selection(
    class_selected,
    keybind_event_listener,
    all_annotation_classes,
    generate_modal_opened,
    edit_modal_opened,
    previous_current_selection,
    control_accordion_state,
):
    """
    This callback is responsible for updating the current class selection when a class is clicked on,
    or when a keybind is pressed.
    """
    current_selection = None
    label_name = None
    if ctx.triggered_id == "keybind-event-listener":
        # user is going to type in the class creation/edit modals and we don't want to trigger this callback using keys
        if generate_modal_opened or any(edit_modal_opened):
            raise PreventUpdate
        if (
            control_accordion_state is not None
            and "run-model" in control_accordion_state
        ):
            raise PreventUpdate
        pressed_key = (
            keybind_event_listener.get("key", None) if keybind_event_listener else None
        )
        if not pressed_key:
            raise PreventUpdate
        # if key pressed is not a valid keybind for class selection
        if pressed_key not in KEYBINDS["classes"]:
            raise PreventUpdate
        selected_color_idx = KEYBINDS["classes"].index(pressed_key)

        # if the key pressed corresponds to a class that doesn't exist
        if selected_color_idx >= len(all_annotation_classes):
            raise PreventUpdate

        current_selection = all_annotation_classes[selected_color_idx]["color"]
        label_name = all_annotation_classes[selected_color_idx]["label"]
        notification = generate_notification_bg_icon_col(
            f"{label_name} class selected", current_selection, "mdi:color"
        )
    else:
        if ctx.triggered_id:
            if len(ctx.triggered) == 1:
                for c in all_annotation_classes:
                    if c["class_id"] == ctx.triggered_id["index"]:
                        current_selection = c["color"]
            # More than one item in the trigger means the trigger comes from adding/deleting a new class
            # make the selected class the last one in the UI
            elif len(all_annotation_classes) > 0:
                current_selection = all_annotation_classes[-1]["color"]
        notification = no_update

    # if the key pressed corresponds to the currently selected class, do nothing
    if previous_current_selection == current_selection:
        raise PreventUpdate

    return current_selection, notification


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
    Output("closed-freeform", "style"),
    Output("circle", "style"),
    Output("rectangle", "style"),
    Output("pan-and-zoom", "style"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Input("closed-freeform", "n_clicks"),
    Input("circle", "n_clicks"),
    Input("rectangle", "n_clicks"),
    Input("pan-and-zoom", "n_clicks"),
    Input("keybind-event-listener", "event"),
    State("annotation-store", "data"),
    State("generate-annotation-class-modal", "opened"),
    State({"type": "edit-annotation-class-modal", "index": ALL}, "opened"),
    State("control-accordion", "value"),
    State("image-viewer", "figure"),
    prevent_initial_call=True,
)
def annotation_mode(
    closed,
    circle,
    rect,
    pan_and_zoom,
    keybind_event_listener,
    annotation_store,
    generate_modal_opened,
    edit_modal_opened,
    control_accordion_state,
    fig,
):
    """
    This callback is responsible for changing the annotation mode and the style of the buttons.
    It also accepts keybinds to change the annotation mode.
    """

    # trigger can be either one of the four buttons (closed-freeform, circle, rectangle, pan-and-zoom or a key press
    trigger = ctx.triggered_id
    pressed_key = (
        keybind_event_listener.get("key", None) if keybind_event_listener else None
    )
    mode = None
    if trigger == "keybind-event-listener":

        if generate_modal_opened or any(edit_modal_opened):
            # user is going to type on this page (on a modal) and we don't want to trigger this callback using keys
            raise PreventUpdate
        if (
            control_accordion_state is not None
            and "run-model" in control_accordion_state
        ):
            raise PreventUpdate

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
        "closed-freeform": inactive,
        "circle": inactive,
        "rectangle": inactive,
        "pan-and-zoom": inactive,
    }

    if mode:
        patched_figure["layout"]["dragmode"] = mode
        annotation_store["dragmode"] = mode
        styles[trigger] = active
        notification = generate_notification(
            ANNOT_NOTIFICATION_MSGS[trigger], "indigo", ANNOT_ICONS[trigger]
        )
    else:
        # Trigger was a button press
        notification = no_update
        if trigger == "closed-freeform" and closed > 0:
            patched_figure["layout"]["dragmode"] = "drawclosedpath"
            annotation_store["dragmode"] = "drawclosedpath"
            styles[trigger] = active
        elif trigger == "circle" and circle > 0:
            patched_figure["layout"]["dragmode"] = "drawcircle"
            annotation_store["dragmode"] = "drawcircle"
            styles[trigger] = active
        elif trigger == "rectangle" and rect > 0:
            patched_figure["layout"]["dragmode"] = "drawrect"
            annotation_store["dragmode"] = "drawrect"
            styles[trigger] = active
        elif trigger == "pan-and-zoom" and pan_and_zoom > 0:
            patched_figure["layout"]["dragmode"] = "pan"
            annotation_store["dragmode"] = "pan"
            styles[trigger] = active

    # disable shape editing when in pan/zoom mode
    # if no shapes have been added yet,
    # none need to be set to not editable
    if "shapes" in fig["layout"]:
        for shape in fig["layout"]["shapes"]:
            shape["editable"] = trigger != "pan-and-zoom"
        patched_figure["layout"]["shapes"] = fig["layout"]["shapes"]
    return (
        patched_figure,
        styles["closed-freeform"],
        styles["circle"],
        styles["rectangle"],
        styles["pan-and-zoom"],
        annotation_store,
        notification,
    )


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
        if new_label == "":
            disable_class_creation = True
            error_msg.append("Label name cannot be empty!")
            error_msg.append(html.Br())
        if new_label == "Unlabeled":
            disable_class_creation = True
            error_msg.append("Label name cannot be 'Unlabeled'")
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
        if new_label == "":
            error_msg.append("Label name cannot be empty!")
            error_msg.append(html.Br())
            edit_disabled = True
        if new_label == "Unlabeled":
            error_msg.append("Label name cannot be 'Unlabeled'!")
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
    Output({"type": "cannot-delete-last-class-modal", "index": MATCH}, "opened"),
    Input({"type": "delete-annotation-class", "index": MATCH}, "n_clicks"),
    Input({"type": "modal-continue-delete-class-btn", "index": MATCH}, "n_clicks"),
    Input({"type": "modal-cancel-delete-class-btn", "index": MATCH}, "n_clicks"),
    Input({"type": "ok-to-not-delete-last-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "cannot-delete-last-class-modal", "index": MATCH}, "opened"),
    State({"type": "delete-annotation-class-modal", "index": MATCH}, "opened"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def open_delete_class_modal(
    remove_class,
    continue_remove_class_modal,
    cancel_remove_class_modal,
    ok_not_delete_modal,
    cannot_delete_modal_opened,
    delete_modal_opened,
    class_to_delete,
    all_annotation_classes,
):
    """
    This callback opens and closes the modal that allows you to relabel an existing annotation class
    and triggers the delete_annotation_class() callback. It prevents the user from deleting the last class.
    """
    if len(all_annotation_classes) == 1:
        return no_update, no_update, not cannot_delete_modal_opened
    modal_title = f"Delete class: {class_to_delete['label']}"
    return not delete_modal_opened, modal_title, no_update


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input({"type": "edit-class-store", "index": ALL}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-selection-slider", "value"),
    State("mask-source-selector", "value"),  # ✅ ADD THIS
    prevent_initial_call=True,
)
def re_draw_annotations_after_editing_class_color(
    hide_show_click, all_annotation_class_store, image_idx, mask_source  # ✅ ADD THIS
):
    """
    After editing a class color, the color is changed in the class-store, but the color change is not reflected
    on the image, so we must regenerate the annotations using Patch() so they show up in the right color.
    """
    fig = Patch()
    image_idx = str(image_idx - 1)

    # ✅ Determine which source to show
    target_source = "original" if mask_source == "annotations" else "sam3"

    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"] and "annotations" in a and image_idx in a["annotations"]:
            # ✅ Filter by source
            filtered_shapes = [
                s
                for s in a["annotations"][image_idx]
                if s.get("source") == target_source
            ]
            all_annotations += filtered_shapes
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
    prevent_initial_call=True,
)
def edit_annotation_class(edit_clicked, new_label, new_color, annotation_class_store):
    """
    This callback edits the name and color of an annotation class by updating class-store metadata. We also trigger
    edit-class-store so we can then redraw the annotations in re_draw_annotations_after_editing_class_color().
    """
    # update store meta data
    annotation_class_store["label"] = new_label
    annotation_class_store["color"] = new_color
    class_color_identifier = {
        "width": "25px",
        "height": "25px",
        "backgroundColor": new_color + "50",
        "margin": "5px",
        "borderRadius": "3px",
        "border": f"2px solid {new_color}",
    }
    # update color in previous annotation data
    for img_idx, annots in annotation_class_store["annotations"].items():
        for annots in annotation_class_store["annotations"][img_idx]:
            annots["line"]["color"] = new_color
            if "fillcolor" in annots:
                annots["fillcolor"] = new_color

    return new_label, class_color_identifier, annotation_class_store, 1, True


@callback(
    Output("annotation-class-label", "value"),
    Output("annotation-class-container", "children", allow_duplicate=True),
    Output("current-class-selection", "data"),
    Output("notifications-container", "children", allow_duplicate=True),
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
    """This callback adds a new annotation class with the same chosen color and label, and creates notification"""
    existing_ids = [annotation["class_id"] for annotation in all_annotations_data]
    current_classes.append(
        annotation_class_item(new_class_color, new_class_label, existing_ids)
    )

    notification = generate_notification_bg_icon_col(
        f"{new_class_label} class created & selected", new_class_color, "mdi:color"
    )
    return "", current_classes, new_class_color, notification


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input({"type": "hide-show-class-store", "index": ALL}, "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-selection-slider", "value"),
    State("mask-source-selector", "value"),  # ✅ ADD THIS
    prevent_initial_call=True,
)
def hide_show_annotations_on_fig(
    hide_show_click, all_annotation_class_store, image_idx, mask_source  # ✅ ADD THIS
):
    """This callback hides or shows all annotations for a given class by Patching the figure accordingly"""
    fig = Patch()
    image_idx = str(image_idx - 1)

    # ✅ Determine which source to show
    target_source = "original" if mask_source == "annotations" else "sam3"

    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"] and "annotations" in a and image_idx in a["annotations"]:
            # ✅ Filter by source
            filtered_shapes = [
                s
                for s in a["annotations"][image_idx]
                if s.get("source") == target_source
            ]
            all_annotations += filtered_shapes
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
    ClientsideFunction(namespace="clientside", function_name="delete_active_shape"),
    Output("image-viewer", "id", allow_duplicate=True),
    Input("keybind-event-listener", "event"),
    Input("keybind-event-listener", "n_events"),
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

    image_shape = global_store["image_shapes"][0]
    annotations = Annotations(all_annotations, image_shape)
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

        notification_title = ANNOT_NOTIFICATION_MSGS["export"]
        notification_message = ANNOT_NOTIFICATION_MSGS["export-msg"]
        notification_color = "green"
    else:
        metadata_file, mask_file = no_update, no_update
        notification_title = ANNOT_NOTIFICATION_MSGS["export-fail"]
        notification_message = ANNOT_NOTIFICATION_MSGS["export-fail-msg"]
        notification_color = "red"
    notification_icon = ANNOT_ICONS["export"]
    notification = generate_notification(
        notification_title,
        notification_color,
        notification_icon,
        notification_message,
    )
    return notification, metadata_file, mask_file


@callback(
    Output("data-modal-save-status", "children"),
    Input("save-annotations", "n_clicks"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-uri", "value"),
    prevent_initial_call=True,
)
def save_data(n_clicks, global_store, all_annotations, image_uri):
    """This callback is responsible for saving the annotation data to the store"""
    if not n_clicks:
        raise PreventUpdate

    if all_annotations:
        # TODO: save store to the server file-user system, this will be changed to DB later
        export_data = {
            "user": USER_NAME,
            "source": image_uri,
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
    State("image-uri", "value"),
    prevent_initial_call=True,
)
def populate_load_annotations_dropdown_menu_options(modal_opened, image_uri):
    """
    This callback populates dropdown window with all saved annotation options for the given project name.
    It then creates buttons with info about the save, which when clicked, loads the data from the server.
    """
    if not modal_opened:
        raise PreventUpdate

    data = tiled_masks.DEV_load_exported_json_data(
        EXPORT_FILE_PATH, USER_NAME, image_uri
    )
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
    State("image-uri", "value"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def load_and_apply_selected_annotations(selected_annotation, image_uri, img_idx):
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
    data = tiled_masks.DEV_load_exported_json_data(
        EXPORT_FILE_PATH, USER_NAME, image_uri
    )
    data = tiled_masks.DEV_filter_json_data_by_timestamp(
        data, str(selected_annotation_timestamp)
    )
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


@callback(
    Output("show-result-overlay-toggle", "disabled"),
    Output("seg-result-opacity-slider", "disabled"),
    Input("show-result-overlay-toggle", "checked"),
    Input("seg-results-train-store", "data"),
    Input("seg-results-inference-store", "data"),
)
def update_result_controls(toggle, seg_result_train, seg_result_inference):
    # Disable opacity slider if result overlay is unchecked
    if ctx.triggered_id == "show-result-overlay-toggle":
        # Must have been enabled to be source of trigger
        disable_toggle = no_update
        # Disable slider if toggle is unchecked
        disable_slider = not toggle
    # Trigger is a change in either a train or inference result
    else:
        if seg_result_train or seg_result_inference:
            disable_toggle = False
            disable_slider = False
        else:
            disable_toggle = True
            disable_slider = True
    return (
        disable_toggle,
        disable_slider,
    )


@callback(
    Output("annotated-slices-selector", "data"),
    Output("annotated-slices-selector", "disabled"),
    Input({"type": "annotation-class-store", "index": ALL}, "data"),
    # TODO check if erasing an annotation via the erase triggers this CB (it should)
)
def update_current_annotated_slices_values(all_classes):
    all_annotated_slices = []
    for a in all_classes:
        all_annotated_slices += list(a["annotations"].keys())
    all_annotated_slices = sorted(list(set(all_annotated_slices)))
    dropdown_values = [
        {"value": int(slice) + 1, "label": f"Slice {str(int(slice) + 1)}"}
        for slice in all_annotated_slices
    ]
    disabled = True if len(dropdown_values) == 0 else False
    return dropdown_values, disabled


@callback(
    Output("model-parameters", "children"),
    Input("model-list", "value"),
)
def update_model_parameters(model_name):
    # Guard against no model selected or available
    if not model_name:
        return html.Div(
            "No models available. Please add segmentation models to MLflow.",
            style={"padding": "10px", "color": "#9EA4AB", "fontSize": "14px"},
        )

    model = models[model_name]
    if model["gui_parameters"]:
        # TODO: Retain old parameters if they exist
        item_list = ParameterItems(
            _id={"type": str(uuid.uuid4())}, json_blob=model["gui_parameters"]
        )
        return item_list
    else:
        return html.Div("Model has no parameters")


@callback(
    Output(
        {"type": MATCH, "param_key": "weights", "layer": "input", "name": "weights"},
        "error",
    ),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    Input(
        {"type": MATCH, "param_key": "weights", "layer": "input", "name": "weights"},
        "value",
    ),
)
def validate_class_weights(all_annotation_classes, weights):

    if weights is None:
        return "Provide a list with a float for each class"

    parsed_weights = weights.strip("[]").split(",")
    try:
        parsed_weights = [float(weight.strip()) for weight in parsed_weights]
        # All elements are floats, check if there are the correct number
        # (number of classes)
        if len(parsed_weights) != len(all_annotation_classes):
            return "This list of floats has the wrong number of entries"
        # All good
        return False
    except ValueError:
        # If there's any error in parsing or validation, return False
        return "Provide a list with a float for each class"


@callback(
    Output(
        {
            "type": MATCH,
            "param_key": "dilation_array",
            "layer": "input",
            "name": "dilation_array",
        },
        "error",
    ),
    Input(
        {
            "type": MATCH,
            "param_key": "dilation_array",
            "layer": "input",
            "name": "dilation_array",
        },
        "value",
    ),
)
def validate_dilation_array(dilation_array):

    if dilation_array is None:
        return "Provide a list of ints for dilation"

    parsed_dilation_array = dilation_array.strip("[]").split(",")
    try:
        parsed_dilation_array = [
            int(array_entry.strip()) for array_entry in parsed_dilation_array
        ]
        if len(parsed_dilation_array) == 0:
            return "Provide a list of ints for dilation"
        # Check if all elements in the list are floats
        return False
    except ValueError:
        # If there's any error in parsing or validation, return False
        return "Provide a list of ints for dilation"


@callback(
    Output("refine-by-sam3", "disabled"),
    Input("image-viewer", "figure"),
    Input("infra-state", "data"),  # ✅ ADD THIS
    State("mask-source-selector", "value"),
    prevent_initial_call=True,
)
def toggle_sam3_button_based_on_rectangles(
    fig, infra_state, mask_source
):  # ✅ ADD infra_state
    """
    Enable SAM3 refinement button if:
    1. SAM3 service is ready
    2. There's at least one rectangle visible
    3. Currently viewing manual annotations (not SAM3 view)
    """
    # Check if SAM3 service is ready
    if infra_state is None or not infra_state.get("sam3_ready", False):
        logger.info("SAM3 button DISABLED (service not ready)")
        return True  # Disabled

    # Only enable for manual annotations view
    if mask_source != "annotations":
        return True  # Disabled for SAM3 view

    # Check if there are any rectangles in the figure
    if "layout" not in fig or "shapes" not in fig["layout"]:
        return True  # No shapes, disable button

    shapes = fig["layout"]["shapes"]

    # Check if there's at least one rectangle
    has_rectangle = any(shape.get("type") == "rect" for shape in shapes)

    if has_rectangle:
        logger.info("SAM3 button ENABLED (rectangles found & service ready)")
        return False  # Enable button
    else:
        logger.info("SAM3 button DISABLED (no rectangles)")
        return True  # Disable button


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Output("sam3-masks-store", "data"),
    Output("mask-source-selector", "data"),
    Output("mask-source-selector", "value"),
    Input("refine-by-sam3", "n_clicks"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-uri", "value"),
    State("sam3-masks-store", "data"),
    prevent_initial_call=True,
)
def refine_bbox_with_sam3(
    n_clicks,
    fig,
    img_idx,
    all_annotation_class_store,
    image_uri,
    existing_sam3_masks,
):
    """
    Refine rectangles using SAM3:
    1. Remove old SAM3 annotations and mark rectangles as "original"
    2. Add NEW SAM3 polygons and mark them as "sam3"
    3. Store fresh masks for training export
    4. Auto-switch to "SAM3 Refined" view
    """
    logger.info("=== SAM3 Polygon Refinement ===")

    if not n_clicks or not fig.get("layout", {}).get("shapes"):
        return no_update, no_update, no_update, no_update, no_update, no_update

    shapes = fig["layout"]["shapes"]
    class_boxes = extract_rectangles_by_class(shapes, all_annotation_class_store)

    if not class_boxes:
        notification = generate_notification(
            "SAM3 Refinement", "orange", ANNOT_ICONS["sam3"], "No rectangles found!"
        )
        return no_update, notification, no_update, no_update, no_update, no_update

    total_boxes = sum(len(data["boxes"]) for data in class_boxes.values())
    logger.info(f"Found {total_boxes} box(es) across {len(class_boxes)} class(es)")

    # Load image
    img_idx -= 1
    slice_key = str(img_idx)

    try:
        image_data = tiled_datasets.get_data_sequence_by_trimmed_uri(image_uri)[img_idx]
        image_pil = load_and_prepare_image(image_data)
    except Exception as e:
        logger.error(f"Error loading image: {e}")
        notification = generate_notification(
            "SAM3 Refinement", "red", ANNOT_ICONS["sam3"], f"Image load error: {e}"
        )
        return no_update, notification, no_update, no_update, no_update, no_update

    # Run SAM3 -> get polygons AND masks
    try:
        all_polygons, all_masks, all_colors, class_results = (
            segment_all_classes_to_polygons(image_pil, class_boxes, sam3_segmenter)
        )

        if all_polygons is None:
            notification = generate_notification(
                "SAM3 Refinement",
                "red",
                ANNOT_ICONS["sam3"],
                "Failed to generate polygons!",
            )
            return no_update, notification, no_update, no_update, no_update, no_update

        # 1. REMOVE old SAM3 annotations and mark rectangles as "original"
        for annotation_class in all_annotation_class_store:
            if slice_key in annotation_class["annotations"]:
                # Keep only non-SAM3 shapes, mark rectangles as "original"
                annotation_class["annotations"][slice_key] = [
                    (
                        {**shape, "source": "original"}
                        if shape.get("type") == "rect" and shape.get("source") is None
                        else shape
                    )
                    for shape in annotation_class["annotations"][slice_key]
                    if shape.get("source") != "sam3"  # Remove old SAM3
                ]
                if not annotation_class["annotations"][slice_key]:
                    del annotation_class["annotations"][slice_key]

        # 2. ADD NEW SAM3 polygons
        for polygon_shape in all_polygons:
            polygon_shape["source"] = "sam3"
            color = polygon_shape["line"]["color"]
            for annotation_class in all_annotation_class_store:
                if annotation_class["color"] == color:
                    if slice_key not in annotation_class["annotations"]:
                        annotation_class["annotations"][slice_key] = []
                    annotation_class["annotations"][slice_key].append(polygon_shape)
                    break

        # 3. Store masks for training (convert to numpy)
        if existing_sam3_masks is None:
            existing_sam3_masks = {}

        slice_mask = convert_sam3_masks_to_numpy(
            all_masks,
            all_colors,
            class_results,
            all_annotation_class_store,
            (image_data.shape[0], image_data.shape[1]),
        )

        existing_sam3_masks[slice_key] = {
            "mask": slice_mask.tolist(),
            "image_shape": [image_data.shape[0], image_data.shape[1]],
            "num_classes": len(all_annotation_class_store),
        }

        logger.info(f"Stored SAM3 mask for slice {slice_key}")

        # 4. Enable SAM3 option in training dropdown
        updated_dropdown_options = [
            {"value": "annotations", "label": "Manual Annotations"},
            {"value": "sam3", "label": "SAM3 Refined"},
        ]

        # 5. Update figure to show ONLY SAM3 polygons (hide original boxes)
        fig_patch = Patch()
        all_shapes = []
        for annotation_class in all_annotation_class_store:
            if (
                annotation_class["is_visible"]
                and slice_key in annotation_class["annotations"]
            ):
                # Show only SAM3 polygons
                sam3_shapes = [
                    shape
                    for shape in annotation_class["annotations"][slice_key]
                    if shape.get("source") == "sam3"
                ]
                all_shapes.extend(sam3_shapes)
        fig_patch["layout"]["shapes"] = all_shapes

        summary = ", ".join(class_results)
        notification = generate_notification(
            "SAM3 Refinement",
            "green",
            ANNOT_ICONS["sam3"],
            f"Refined {total_boxes} box(es): {summary}. Showing refined polygons.",
        )

        logger.info("=== SAM3 Complete ===")
        return (
            fig_patch,
            notification,
            all_annotation_class_store,
            existing_sam3_masks,
            updated_dropdown_options,
            "sam3",  # Auto-select SAM3 in dropdown
        )

    except Exception as e:
        logger.error(f"SAM3 error: {e}", exc_info=True)
        notification = generate_notification(
            "SAM3 Refinement", "red", ANNOT_ICONS["sam3"], f"Error: {e}"
        )
        return no_update, notification, no_update, no_update, no_update, no_update


@callback(
    Output("sam3-masks-store", "data", allow_duplicate=True),
    Output("mask-source-selector", "data", allow_duplicate=True),
    Output("mask-source-selector", "value", allow_duplicate=True),
    Input("image-uri", "value"),
    Input("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def clear_sam3_on_image_change(image_uri, slider_value):
    """
    Clear SAM3 masks and reset dropdown when changing images or slices
    """
    updated_dropdown_options = [
        {"value": "annotations", "label": "Manual Annotations"},
        {"value": "sam3", "label": "SAM3 Refined", "disabled": True},
    ]

    return {}, updated_dropdown_options, "annotations"


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("mask-source-selector", "value"),
    State("image-selection-slider", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def toggle_annotation_display(mask_source, img_idx, all_annotation_class_store):
    """
    Toggle between showing original annotations (boxes) vs SAM3 refined (polygons)

    When mask_source == "annotations": Show ONLY original boxes
    When mask_source == "sam3": Show ONLY SAM3 polygons
    """
    if not mask_source:
        raise PreventUpdate

    img_idx -= 1
    slice_key = str(img_idx)

    fig_patch = Patch()
    all_shapes = []

    for annotation_class in all_annotation_class_store:
        if not annotation_class["is_visible"]:
            continue
        if slice_key not in annotation_class["annotations"]:
            continue

        if mask_source == "sam3":
            # Show ONLY SAM3 polygons
            sam3_shapes = [
                shape
                for shape in annotation_class["annotations"][slice_key]
                if shape.get("source") == "sam3"
            ]
            all_shapes.extend(sam3_shapes)
        else:
            # Show ONLY original boxes (and any manually drawn shapes without source tag)
            original_shapes = [
                shape
                for shape in annotation_class["annotations"][slice_key]
                if shape.get("source") != "sam3"
            ]
            all_shapes.extend(original_shapes)

    fig_patch["layout"]["shapes"] = all_shapes
    fig_patch["layout"][
        "uirevision"
    ] = mask_source  # Force update by changing uirevision

    return fig_patch
