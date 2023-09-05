import os
import time
from dash import (
    Input,
    Output,
    dcc,
    State,
    callback,
    Patch,
    ALL,
    MATCH,
    ctx,
    clientside_callback,
    no_update,
)
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import json
from utils.annotations import Annotations
from components.annotation_class import annotation_class_item
from constants import KEYBINDS, ANNOT_ICONS, ANNOT_NOTIFICATION_MSGS
import json
from utils.data_utils import (
    DEV_load_exported_json_data,
    DEV_filter_json_data_by_timestamp,
)


# TODO - temporary local file path and user for annotation saving and exporting
EXPORT_FILE_PATH = "data/exported_annotation_data.json"
USER_NAME = "user1"

# Create an empty file if it doesn't exist
if not os.path.exists(EXPORT_FILE_PATH):
    with open(EXPORT_FILE_PATH, "w") as f:
        pass
# TODO - temporary local file path and user for annotation saving and exporting
import random


@callback(
    Output("current-class-selection", "data", allow_duplicate=True),
    Input({"type": "annotation-class", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def update_current_class_selection(class_selected):
    current_selection = None
    if ctx.triggered_id:
        if len(ctx.triggered) == 1:
            current_selection = ctx.triggered_id["index"]
        # if more than one items in the trigger -> means the trigger comes from adding a new class.
        # we dont want to reset the current selection in this case
        else:
            current_selection = no_update
    return current_selection


@callback(
    Output({"type": "annotation-class", "index": ALL}, "style"),
    Input("current-class-selection", "data"),
    State({"type": "annotation-class", "index": ALL}, "id"),
)
def update_selected_class_style(selected_class, current_ids):
    """This callback is responsible for updating the style of the selected annot class to makw it appear
    like it has been "selected" """
    default_style = {
        "border": "1px solid #EAECEF",
        "borderRadius": "3px",
        "marginBottom": "4px",
        "display": "flex",
        "justifyContent": "space-between",
    }
    selected_style = {
        "border": "3px solid rgb(230,230,230)",
        "borderRadius": "3px",
        "marginBottom": "4px",
        "display": "flex",
        "justifyContent": "space-between",
        "backgroundColor": "rgb(240,240,240)",
    }
    ids = [c["index"] for c in current_ids]
    if selected_class in ids:
        index = ids.index(selected_class)
        styles = [default_style] * len(ids)
        styles[index] = selected_style
        return styles
    else:
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
    Output("current-ann-mode", "data", allow_duplicate=True),
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
):
    """
    This callback is responsible for changing the annotation mode and the style of the buttons.
    It also accepts keybinds to change the annotation mode.
    """
    if generate_modal_opened:
        # user is going to type on this page and we don't want to trigger this callback using keys
        raise PreventUpdate
    # if the image is loading stop the callback when keybinds are pressed
    if figure_overlay_z_index != -1:
        raise PreventUpdate

    key_modes = {
        KEYBINDS["open-freeform"]: ("drawopenpath", "open-freeform"),
        KEYBINDS["closed-freeform"]: ("drawclosedpath", "closed-freeform"),
        KEYBINDS["circle"]: ("drawcircle", "circle"),
        KEYBINDS["rectangle"]: ("drawrect", "rectangle"),
        KEYBINDS["line"]: ("drawline", "line"),
        KEYBINDS["pan-and-zoom"]: ("pan", "pan-and-zoom"),
        KEYBINDS["erase"]: ("eraseshape", "eraser"),
    }

    triggered = ctx.triggered_id
    pressed_key = (
        keybind_event_listener.get("key", None) if keybind_event_listener else None
    )

    if pressed_key in key_modes and triggered == "keybind-event-listener":
        mode, triggered = key_modes[pressed_key]
    else:
        # if the callback was triggered by pressing a key that is not in the `key_modes`, stop the callback
        if triggered == "keybind-event-listener":
            raise PreventUpdate
        mode = None

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
        styles[triggered] = active
    else:
        if triggered == "open-freeform" and open > 0:
            patched_figure["layout"]["dragmode"] = "drawopenpath"
            annotation_store["dragmode"] = "drawopenpath"
            styles[triggered] = active
        elif triggered == "closed-freeform" and closed > 0:
            patched_figure["layout"]["dragmode"] = "drawclosedpath"
            annotation_store["dragmode"] = "drawclosedpath"
            styles[triggered] = active
        elif triggered == "line" and line > 0:
            patched_figure["layout"]["dragmode"] = "drawline"
            annotation_store["dragmode"] = "drawline"
            styles[triggered] = active
        elif triggered == "circle" and circle > 0:
            patched_figure["layout"]["dragmode"] = "drawcircle"
            annotation_store["dragmode"] = "drawcircle"
            styles[triggered] = active
        elif triggered == "rectangle" and rect > 0:
            patched_figure["layout"]["dragmode"] = "drawrect"
            annotation_store["dragmode"] = "drawrect"
            styles[triggered] = active
        elif triggered == "eraser" and erase_annotation > 0:
            patched_figure["layout"]["dragmode"] = "eraseshape"
            annotation_store["dragmode"] = "eraseshape"
            styles[triggered] = active
        elif triggered == "pan-and-zoom" and pan_and_zoom > 0:
            patched_figure["layout"]["dragmode"] = "pan"
            annotation_store["dragmode"] = "pan"
            styles[triggered] = active

    notification = dmc.Notification(
        title=ANNOT_NOTIFICATION_MSGS[triggered],
        message="",
        color="indigo",
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        icon=DashIconify(icon=ANNOT_ICONS[triggered], width=40),
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
        triggered,
        notification,
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
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("current-class-selection", "data"),
    Input("image-selection-slider", "value"),
    Input("keybind-event-listener", "event"),
    State("generate-annotation-class-modal", "opened"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def annotation_color(
    current_color,
    slider,
    keybind_event_listener,
    generate_modal_opened,
    annotation_store,
):
    """
    This callback is responsible for changing the color of the brush.
    """
    if ctx.triggered_id == "keybind-event-listener":
        if generate_modal_opened:  # or edit_annotation_modal_opened:
            # user is going to type on this page and we don't want to trigger this callback using keys
            raise PreventUpdate
        pressed_key = (
            keybind_event_listener.get("key", None) if keybind_event_listener else None
        )
        if not pressed_key:
            raise PreventUpdate
        if pressed_key not in KEYBINDS["classes"]:
            # if key pressed is not a valid keybind for class selection
            raise PreventUpdate
        selected_color_idx = KEYBINDS["classes"].index(pressed_key)

        # if selected_color_idx >= len(current_style):
        #     # if the key pressed corresponds to a class that doesn't exist
        #     raise PreventUpdate
    print(current_color)
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = current_color
    patched_figure["layout"]["newshape"]["line"]["color"] = current_color
    print("here")
    print(ctx.triggered_id)
    print("----")

    return patched_figure, annotation_store


@callback(
    Output("delete-all-warning", "opened"),
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Input("clear-all", "n_clicks"),
    Input("modal-cancel-delete-button", "n_clicks"),
    Input("modal-continue-delete-button", "n_clicks"),
    State("delete-all-warning", "opened"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def open_warning_modal(
    delete, cancel_delete, continue_delete, opened, all_class_annotations
):
    """Opens and closes the modal that warns you when you're deleting all annotations"""
    if ctx.triggered_id in ["clear-all", "modal-cancel-delete-button"]:
        print("here!")
        return not opened, all_class_annotations
    if ctx.triggered_id == "modal-continue-delete-button":
        for a in all_class_annotations:
            # TODO: implement deletion
            print(a)
        return not opened, all_class_annotations
    else:
        return no_update, all_class_annotations


@callback(
    Output("generate-annotation-class-modal", "opened"),
    Output("create-annotation-class", "disabled"),
    Output("bad-label-color", "children"),
    Input("generate-annotation-class", "n_clicks"),
    Input("create-annotation-class", "n_clicks"),
    Input("annotation-class-label", "value"),
    State("generate-annotation-class-modal", "opened"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def open_annotation_class_modal(generate, create, new_label, opened, annotation_store):
    """Opens and closes the modal that is used to create a new annotation class"""
    if ctx.triggered_id in "annotation-class-label":
        # TODO: update so this uses individual class store. label mapping is not deprecated
        current_classes = []
        if new_label in current_classes:
            return no_update, True, "Class name already in use!"
        else:
            return no_update, False, ""
    return not opened, False, ""


@callback(
    Output({"type": "edit-annotation-class-modal", "index": MATCH}, "opened"),
    Input({"type": "edit-annotation-class", "index": MATCH}, "n_clicks"),
    Input({"type": "relabel-annotation-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "edit-annotation-class-modal", "index": MATCH}, "opened"),
    prevent_initial_call=True,
)
def open_edit_class_modal(edit_button, edit_modal, opened):
    """Opens and closes the modal that allows you to relabel an existing annotation class"""
    return not opened


@callback(
    Output({"type": "delete-annotation-class-modal", "index": MATCH}, "opened"),
    Input({"type": "delete-annotation-class", "index": MATCH}, "n_clicks"),
    Input({"type": "remove-annotation-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "delete-annotation-class-modal", "index": MATCH}, "opened"),
    prevent_initial_call=True,
)
def open_delete_class_modal(remove_class, remove_class_modal, opened):
    """Opens and closes the modal that allows you to relabel an existing annotation class"""
    return not opened


@callback(
    Output({"type": "annotation-class-label", "index": MATCH}, "children"),
    Output({"type": "annotation-class-store", "index": MATCH}, "data"),
    Output({"type": "edit-annotation-class-text-input", "index": MATCH}, "value"),
    Input({"type": "relabel-annotation-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "edit-annotation-class-text-input", "index": MATCH}, "value"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def edit_annotation_class(edit_clicked, new_label, annotation_class_store):
    """edit the name of an annotation class"""
    annotation_class_store["label"] = new_label
    return new_label, annotation_class_store, ""


@callback(
    Output("annotation-class-label", "value"),
    Output("annotation-class-container", "children", allow_duplicate=True),
    Output("current-class-selection", "data"),
    Input("create-annotation-class", "n_clicks"),
    State("annotation-class-container", "children"),
    State("annotation-class-label", "value"),
    State("annotation-class-colorpicker", "value"),
    prevent_initial_call=True,
)
def add_annotation_class(
    create,
    current_classes,
    new_class_label,
    new_class_color,
):
    """adds a new annotation class with the same chosen color and label"""
    current_classes.append(annotation_class_item(new_class_color, new_class_label))
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
    """hides or shows all annotations for a given class by Patching the figure"""
    fig = Patch()
    image_idx = str(image_idx - 1)
    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"]:
            if "annotations" in a:
                if image_idx in a["annotations"]:
                    all_annotations = all_annotations + a["annotations"][image_idx]
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
    """Updates both the annotation-class-store (which contains the annotation info) and the hide-show-class-store
    which is only used to trigger the callback that will actually patch the figure. Also update the hide/show icon accordingly
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
def delete_annotation_class(
    is_deleted,
    all_classes,
):
    """delete the class from memory using the color from the deleted-class-store"""
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
    Input({"type": "remove-annotation-class-btn", "index": MATCH}, "n_clicks"),
    State({"type": "annotation-class-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def clear_annotation_class(
    remove,
    annotation_class_store,
):
    """update the deleted-class-store with the color of the class to delete"""
    deleted_class = annotation_class_store["color"]
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
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        icon=DashIconify(icon="entypo:export"),
    )
    return notification, metadata_file, mask_file


@callback(
    Output("data-modal-save-status", "children"),
    Input("save-annotations", "n_clicks"),
    State("annotation-store", "data"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def save_data(n_clicks, annotation_store, image_src):
    """
    This callback is responsible for saving the annotation data to the store.
    """
    if not n_clicks:
        raise PreventUpdate
    if annotation_store["annotations"] == {}:
        return "No annotations to save!"

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

    # TODO : when quering from the server, get (annotation save time) for user, source, order by time
    data = DEV_load_exported_json_data(EXPORT_FILE_PATH, USER_NAME, image_src)
    if not data:
        return "No annotations found for the selected data source."
    # TODO : when quering from the server, load data for user, source, order by time

    buttons = []
    for i, data_json in enumerate(data):
        no_of_annotations = 0
        for key, annotation_list in data_json["data"]["annotations"].items():
            no_of_annotations += len(annotation_list)

        number_of_annotated_images = len(data_json["data"]["annotations"])
        buttons.append(
            dmc.Button(
                f"{no_of_annotations} annotations across {number_of_annotated_images} images, created at {data_json['time']}",
                id={"type": "load-server-annotations", "index": data_json["time"]},
                variant="light",
            )
        )

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
    img_idx -= 1  # dmc.Slider starts from 1, but we need to start from 0

    selected_annotation_timestamp = json.loads(
        ctx.triggered[0]["prop_id"].split(".")[0]
    )["index"]

    # TODO : when quering from the server, load (data) for user, source, time
    data = DEV_load_exported_json_data(EXPORT_FILE_PATH, USER_NAME, image_src)
    data = DEV_filter_json_data_by_timestamp(data, str(selected_annotation_timestamp))
    data = data[0]["data"]
    # TODO : when quering from the server, load (data) for user, source, time
    patched_figure = Patch()
    if str(img_idx) in data["annotations"]:
        patched_figure["layout"]["shapes"] = data["annotations"][str(img_idx)]
    else:
        patched_figure["layout"]["shapes"] = []

    return patched_figure, data, False


@callback(
    Output("drawer-controls", "opened"),
    Input("drawer-controls-open-button", "n_clicks"),
)
def open_controls_drawer(n_clicks):
    return True


@callback(
    Output("drawer-controls-open-button", "style"),
    Input("drawer-controls", "opened"),
    prevent_initial_call=True,
)
def open_controls_drawer(is_opened):
    if is_opened:
        return {"display": "none"}
    return {}
