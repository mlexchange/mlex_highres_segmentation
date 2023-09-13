import random

import dash
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
from dash import (
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
)

clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="get_container_size"),
    Output("screen-size", "data"),
    Input("url", "href"),
)


@callback(
    Output("image-viewer", "figure"),
    Output("image-viewfinder", "figure"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer-loading", "zIndex", allow_duplicate=True),
    Output("data-selection-controls", "children", allow_duplicate=True),
    Output("image-transformation-controls", "children", allow_duplicate=True),
    Output("annotations-controls", "children", allow_duplicate=True),
    Output("image-metadata", "data"),
    Input("image-selection-slider", "value"),
    Input("show-result-overlay", "checked"),
    State("project-name-src", "value"),
    State("paintbrush-width", "value"),
    State("annotation-class-selection", "children"),
    State("annotation-store", "data"),
    State("result-selector", "value"),
    State("image-metadata", "data"),
    State("screen-size", "data"),
    prevent_initial_call=True,
)
def render_image(
    image_idx,
    toggle_result,
    project_name,
    annotation_width,
    annotation_colors,
    annotation_store,
    result_name,
    image_metadata,
    screen_size,
):
    if image_idx:
        image_idx -= 1  # slider starts at 1, so subtract 1 to get the correct index
        tf = get_data_sequence_by_name(project_name)[image_idx]
        if toggle_result:
            result = get_data_sequence_by_name(result_name)[image_idx]
            tf = 0.1 * tf + 0.9 * result

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
    # set the default annotation style
    for color_opt in annotation_colors:
        if color_opt["props"]["style"]["border"] != "1px solid":
            color = color_opt["props"]["style"]["background-color"]
    fig.update_layout(
        newshape=dict(
            line=dict(color=color, width=annotation_width),
            fillcolor=color,
        )
    )

    if annotation_store:
        fig["layout"]["dragmode"] = annotation_store["dragmode"]
        if not annotation_store["visible"]:
            fig["layout"]["shapes"] = []
        else:
            if str(image_idx) in annotation_store["annotations"]:
                fig["layout"]["shapes"] = annotation_store["annotations"][
                    str(image_idx)
                ]

        view = annotation_store["view"]
        if view:
            if "xaxis_range_0" in view and annotation_store["active_img_shape"] == list(
                tf.shape
            ):
                fig.update_layout(
                    xaxis=dict(range=[view["xaxis_range_0"], view["xaxis_range_1"]]),
                    yaxis=dict(range=[view["yaxis_range_0"], view["yaxis_range_1"]]),
                )

    if (
        project_name != image_metadata["name"]
        or image_metadata["name"] is None
        and screen_size
    ):
        curr_image_metadata = {"size": tf.shape, "name": project_name}
        fig = resize_canvas(
            tf.shape[0], tf.shape[1], screen_size["H"], screen_size["W"], fig
        )
        view = None
    else:
        view = annotation_store["view"]

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
        dash.no_update,
        dash.no_update,
        dash.no_update,
        curr_image_metadata,
    )


@callback(
    Output("image-selection-slider", "value", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Input("keybind-event-listener", "n_events"),
    Input("keybind-event-listener", "event"),
    State("image-selection-slider", "value"),
    State("image-selection-slider", "max"),
    prevent_initial_call=True,
)
def keybind_image_slider(n_events, keybind_event_listener, current_slice, max_slice):
    """Allows user to use left/right arrow keys to navigate through images"""
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
    When relayoutData is triggered, update the viewfinder box to match the new view position of the image (inlude zooming).
    The viewfinder box is downsampled to match the size of the viewfinder.
    The viewfinder box is containen within the figure layout, so that if the user zooms out/pans away, they will still be able to see the viewfinder box.
    """
    # Callback is triggered when the image is first loaded, but the annotation_store is not yet populated so we need to prevent the update
    if not annotation_store["active_img_shape"]:
        raise dash.exceptions.PreventUpdate
    patched_fig = Patch()

    DOWNSCALED_img_max_height, DOWNSCALED_img_max_width = get_view_finder_max_min(
        annotation_store["image_ratio"]
    )

    if "xaxis.range[0]" not in relayout_data:
        raise dash.exceptions.PreventUpdate
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
    Output("annotation-store", "data", allow_duplicate=True),
    Input("image-viewer", "relayoutData"),
    State("image-selection-slider", "value"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def locally_store_annotations(relayout_data, img_idx, annotation_store):
    """
    Upon finishing relayout event (drawing, but it also includes panning, zooming),
    this function takes the annotation shapes, and stores it in the dcc.Store, which is then used elsewhere
    to preserve drawn annotations, or to save them.
    """
    if "shapes" in relayout_data:
        annotation_store["annotations"][str(img_idx - 1)] = relayout_data["shapes"]
    if "xaxis.range[0]" in relayout_data:
        annotation_store["view"]["xaxis_range_0"] = relayout_data["xaxis.range[0]"]
        annotation_store["view"]["xaxis_range_1"] = relayout_data["xaxis.range[1]"]
        annotation_store["view"]["yaxis_range_0"] = relayout_data["yaxis.range[0]"]
        annotation_store["view"]["yaxis_range_1"] = relayout_data["yaxis.range[1]"]

    return annotation_store


@callback(
    Output("image-selection-slider", "min"),
    Output("image-selection-slider", "max"),
    Output("image-selection-slider", "value"),
    Output("image-selection-slider", "disabled"),
    Output("annotation-store", "data"),
    Output("data-selection-controls", "children"),
    Output("image-transformation-controls", "children"),
    Output("annotations-controls", "children"),
    Input("project-name-src", "value"),
    State("annotation-store", "data"),
)
def update_slider_values(project_name, annotation_store):
    """
    When the data source is loaded, this callback will set the slider values and chain call
        "update_selection_and_image" callback which will update image and slider selection component
    It also resets "annotation-store" data to {} so that existing annotations don't carry over to the new project.

    ## todo - change Input("project-name-src", "data") to value when image-src will contain buckets of data and not just one image
    ## todo - eg, when a different image source is selected, update slider values which is then used to select image within that source
    """
    # Retrieve data shape if project_name is valid and points to a 3d array
    data_shape = (
        get_data_shape_by_name(project_name) if not project_name is None else None
    )
    disable_slider = data_shape is None
    if not disable_slider:
        # TODO: Assuming that all slices have the same image shape
        annotation_store["image_shapes"] = [(data_shape[1], data_shape[2])]
    min_slider_value = 0 if disable_slider else 1
    max_slider_value = 0 if disable_slider else data_shape[0]
    slider_value = 0 if disable_slider else 1
    annotation_store["annotations"] = {}
    annotation_store["view"] = {}
    annotation_store["image_ratio"] = 1
    return (
        min_slider_value,
        max_slider_value,
        slider_value,
        disable_slider,
        annotation_store,
        # No update is needed for the 'children' of the control components
        # since we just want to trigger the loading overlay with this callback
        dash.no_update,
        dash.no_update,
        dash.no_update,
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
    previous_image, next_image, slider_value, slider_min, slider_max
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
