import random

import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
from dash import (
    ALL,
    ClientsideFunction,
    Input,
    Output,
    Patch,
    State,
    callback,
    clientside_callback,
    ctx,
)
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from constants import ANNOT_ICONS, ANNOT_NOTIFICATION_MSGS, KEYBINDS
from utils.data_utils import get_data_sequence_by_name, get_data_shape_by_name
from utils.plot_utils import (
    create_viewfinder,
    downscale_view,
    get_view_finder_max_min,
    resize_canvas,
    resize_canvas_with_zoom,
)


@callback(
    Output("image-viewer", "figure"),
    Output("image-viewfinder", "figure"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer-loading", "zIndex", allow_duplicate=True),
    Output("image-metadata", "data"),
    Input("image-selection-slider", "value"),
    Input("window-resize", "width"),
    Input("window-resize", "height"),
    Input("reset-view", "n_clicks"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    State("annotation-store", "data"),
    State("image-metadata", "data"),
    State("current-class-selection", "data"),
    prevent_initial_call=True,
)
def render_image(
    image_idx,
    screen_width,
    screen_height,
    reset_view,
    all_annotation_class_store,
    project_name,
    annotation_store,
    image_metadata,
    current_color,
):
    if image_idx:
        image_idx -= 1  # slider starts at 1, so subtract 1 to get the correct index
        tf = get_data_sequence_by_name(project_name)[image_idx]
    else:
        tf = np.zeros((500, 500))

    fig = px.imshow(tf, binary_string=True)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        dragmode="drawopenpath",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(hovertemplate=None, hoverinfo="skip")
    fig["layout"]["newshape"]["fillcolor"] = current_color
    fig["layout"]["newshape"]["line"]["color"] = current_color
    view = None
    if annotation_store:
        fig["layout"]["dragmode"] = annotation_store["dragmode"]
        all_annotations = []
        for a_class in all_annotation_class_store:
            if str(image_idx) in a_class["annotations"] and a_class["is_visible"]:
                all_annotations += a_class["annotations"][str(image_idx)]

        fig["layout"]["shapes"] = all_annotations
        view = annotation_store["view"]

    if screen_width and screen_height:
        if view and ctx.triggered_id != "reset-view":
            # we have a zoom + window size to take into account
            if "xaxis_range_0" in view:
                fig, view = resize_canvas_with_zoom(
                    view, screen_height, screen_width, fig
                )
        else:
            # no zoom level to take into account, window size only, also used for reset view case
            fig = resize_canvas(
                tf.shape[0], tf.shape[1], screen_height, screen_width, fig
            )
            view = {}
    patched_annotation_store = Patch()
    patched_annotation_store["active_img_shape"] = list(tf.shape)
    fig_loading_overlay = -1

    image_ratio = round(tf.shape[1] / tf.shape[0], 2)
    patched_annotation_store["image_ratio"] = image_ratio
    DOWNSCALED_img_max_height, DOWNSCALED_img_max_width = get_view_finder_max_min(
        image_ratio
    )
    fig_viewfinder = create_viewfinder(
        tf, (DOWNSCALED_img_max_height, DOWNSCALED_img_max_width), view
    )

    # No update is needed for the 'children' of the control components
    # since we just want to trigger the loading overlay with this callback
    if project_name != image_metadata["name"] or image_metadata["name"] is None:
        curr_image_metadata = {"size": tf.shape, "name": project_name}
    else:
        curr_image_metadata = dash.no_update
    return (
        fig,
        fig_viewfinder,
        patched_annotation_store,
        fig_loading_overlay,
        curr_image_metadata,
    )


@callback(
    Output("image-selection-slider", "value", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Input("keybind-event-listener", "n_events"),
    Input("keybind-event-listener", "event"),
    State("image-selection-slider", "value"),
    State("image-selection-slider", "max"),
    State("generate-annotation-class-modal", "opened"),
    State({"type": "edit-annotation-class-modal", "index": ALL}, "opened"),
    prevent_initial_call=True,
)
def keybind_image_slider(
    n_events,
    keybind_event_listener,
    current_slice,
    max_slice,
    generate_modal_opened,
    edit_modal_opened,
):
    """Allows user to use left/right arrow keys to navigate through images"""
    if generate_modal_opened or any(edit_modal_opened):
        raise PreventUpdate

    pressed_key = (
        keybind_event_listener.get("key", None) if keybind_event_listener else None
    )
    if not pressed_key:
        raise PreventUpdate
    if pressed_key not in [KEYBINDS["slice-right"], KEYBINDS["slice-left"]]:
        # if key pressed is not a valid keybind for right/left slice
        raise PreventUpdate

    if pressed_key == KEYBINDS["slice-left"]:
        if current_slice == 1:
            message = "No more images to the left"
            new_slice = dash.no_update
            icon = "pajamas:warning-solid"
        else:
            new_slice = current_slice - 1
            message = f"{ANNOT_NOTIFICATION_MSGS['slice-left']} ({new_slice}) selected"
            icon = ANNOT_ICONS["slice-left"]
    elif pressed_key == KEYBINDS["slice-right"]:
        if current_slice == max_slice:
            message = "No more images to the right"
            new_slice = dash.no_update
            icon = "pajamas:warning-solid"
        else:
            new_slice = current_slice + 1
            message = f"{ANNOT_NOTIFICATION_MSGS['slice-right']} ({new_slice}) selected"
            icon = ANNOT_ICONS["slice-right"]

    notification = dmc.Notification(
        title=message,
        message="",
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        icon=DashIconify(icon=icon, width=30),
        styles={
            "icon": {
                "height": "50px",
                "width": "50px",
            }
        },
    )

    return new_slice, notification


@callback(
    Output("image-viewfinder", "figure", allow_duplicate=True),
    Input("image-viewer", "relayoutData"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def update_viewfinder(relayout_data, annotation_store):
    """
    When relayoutData is triggered, update the viewfinder box to match the
    new view position of the image (including zooming). The viewfinder box is
    downsampled to match the size of the viewfinder. The viewfinder box is
    contained within the figure layout, so that if the user zooms out/pans away,
    they will still be able to see the viewfinder box.
    """
    # Callback is triggered when the image is first loaded, but the annotation_store is not yet populated so we need to prevent the update
    if not annotation_store["active_img_shape"]:
        raise PreventUpdate
    patched_fig = Patch()

    DOWNSCALED_img_max_height, DOWNSCALED_img_max_width = get_view_finder_max_min(
        annotation_store["image_ratio"]
    )

    if "xaxis.range[0]" not in relayout_data:
        raise PreventUpdate
    else:
        x0, y0, x1, y1 = downscale_view(
            relayout_data["xaxis.range[0]"],
            relayout_data["yaxis.range[0]"],
            relayout_data["xaxis.range[1]"],
            relayout_data["yaxis.range[1]"],
            annotation_store["active_img_shape"],
            (DOWNSCALED_img_max_height, DOWNSCALED_img_max_width),
        )
        patched_fig["layout"]["shapes"][0]["x0"] = x0 if x0 > 0 else 0
        patched_fig["layout"]["shapes"][0]["y0"] = (
            y0 if y0 < DOWNSCALED_img_max_height else DOWNSCALED_img_max_height
        )
        patched_fig["layout"]["shapes"][0]["x1"] = (
            x1 if x1 < DOWNSCALED_img_max_width else DOWNSCALED_img_max_width
        )
        patched_fig["layout"]["shapes"][0]["y1"] = y1 if y1 > 0 else 0
    return patched_fig


clientside_callback(
    """
    function EnableImageLoadingOverlay(zIndex) {
        return 9999;
    }
    """,
    Output("image-viewer-loading", "zIndex"),
    Input("image-selection-slider", "value"),
)


@callback(
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("image-viewer", "relayoutData"),
    State("image-selection-slider", "value"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("current-class-selection", "data"),
    prevent_initial_call=True,
)
def locally_store_annotations(
    relayout_data, img_idx, annotation_store, all_annotation_class_store, current_color
):
    """
    Upon finishing a relayout event (drawing, panning or zooming), this function takes the
    currently drawn shapes or zoom/pan data, and stores the lastest added shape to the
    appropriate class-annotation-store, or the image pan/zoom position to the anntations-store.
    """
    img_idx = str(img_idx - 1)
    if "shapes" in relayout_data:
        last_shape = relayout_data["shapes"][-1]
        for a_class in all_annotation_class_store:
            if a_class["color"] == current_color:
                if img_idx in a_class["annotations"]:
                    a_class["annotations"][img_idx].append(last_shape)
                else:
                    a_class["annotations"][img_idx] = [last_shape]
    if "xaxis.range[0]" in relayout_data:
        annotation_store["view"]["xaxis_range_0"] = relayout_data["xaxis.range[0]"]
        annotation_store["view"]["xaxis_range_1"] = relayout_data["xaxis.range[1]"]
        annotation_store["view"]["yaxis_range_0"] = relayout_data["yaxis.range[0]"]
        annotation_store["view"]["yaxis_range_1"] = relayout_data["yaxis.range[1]"]

    return all_annotation_class_store, annotation_store


@callback(
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Input("project-name-src", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def clear_annotations_on_dataset_change(change_project, all_annotation_class_store):
    """
    This callback is responsible for removing the annotations from every annotation-class-store
    when the dataset is changed (when a new image is selected)
    """
    for a in all_annotation_class_store:
        a["annotations"] = {}
    return all_annotation_class_store


@callback(
    Output("image-selection-slider", "min"),
    Output("image-selection-slider", "max"),
    Output("image-selection-slider", "value"),
    Output("image-selection-slider", "disabled"),
    Output("annotation-store", "data"),
    Input("project-name-src", "value"),
    State("annotation-store", "data"),
)
def update_slider_values(project_name, annotation_store):
    """
    When the data source is loaded, this callback will set the slider values and chain call
    "update_selection_and_image" callback which will update image and slider selection component.
    """
    # Retrieve data shape if project_name is valid and points to a 3d array
    data_shape = get_data_shape_by_name(project_name) if project_name else None
    disable_slider = data_shape is None
    if not disable_slider:
        # TODO: Assuming that all slices have the same image shape
        annotation_store["image_shapes"] = [(data_shape[1], data_shape[2])]
    min_slider_value = 0 if disable_slider else 1
    max_slider_value = 0 if disable_slider else data_shape[0]
    slider_value = 0 if disable_slider else 1
    annotation_store["view"] = {}
    annotation_store["image_ratio"] = 1
    return (
        min_slider_value,
        max_slider_value,
        slider_value,
        disable_slider,
        annotation_store,
    )


@callback(
    Output("image-selection-slider", "value", allow_duplicate=True),
    Output("image-selection-previous", "disabled"),
    Output("image-selection-next", "disabled"),
    Output("image-selection-text", "children"),
    Input("image-selection-previous", "n_clicks"),
    Input("image-selection-next", "n_clicks"),
    Input("image-selection-slider", "value"),
    State("image-selection-slider", "min"),
    State("image-selection-slider", "max"),
    prevent_initial_call=True,
)
def update_selection_and_image(
    previous_image,
    next_image,
    slider_value,
    slider_min,
    slider_max,
):
    """
    This callback will update the slider value and the image when the user clicks on the previous or next image buttons
    """
    new_slider_value = slider_value
    if ctx.triggered[0]["prop_id"] == "image-selection-previous.n_clicks":
        new_slider_value -= 1
    elif ctx.triggered[0]["prop_id"] == "image-selection-next.n_clicks":
        new_slider_value += 1
    disable_previous_image = new_slider_value == slider_min
    disable_next_image = new_slider_value == slider_max
    if new_slider_value == slider_value:
        return (
            dash.no_update,
            disable_previous_image,
            disable_next_image,
            f"Slice {new_slider_value}",
        )
    return (
        new_slider_value,
        disable_previous_image,
        disable_next_image,
        f"Slice {new_slider_value}",
    )
