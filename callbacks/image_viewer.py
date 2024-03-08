import dash
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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

from constants import ANNOT_ICONS, ANNOT_NOTIFICATION_MSGS, KEYBINDS
from utils.data_utils import tiled_datasets, tiled_results
from utils.plot_utils import (
    create_viewfinder,
    downscale_view,
    generate_notification,
    generate_segmentation_colormap,
    get_view_finder_max_min,
    resize_canvas,
)

clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="get_container_size"),
    Output("screen-size", "data"),
    Input("url", "href"),
)


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("show-result-overlay-toggle", "checked"),
    Input("seg-result-opacity-slider", "value"),
    prevent_initial_call=True,
)
def hide_show_segmentation_overlay(toggle_seg_result, opacity):
    """
    This callback is responsible for hiding or showing the segmentation results overlay
    by making the opacity 0 (given that this image has already been rendered in the render_image callback).
    This callback also adjusts the opactiy of the results based on the opacity slider.
    """
    fig = Patch()
    fig["data"][1]["opacity"] = opacity / 100
    if ctx.triggered_id == "show-result-overlay-toggle" and not toggle_seg_result:
        fig["data"][1]["opacity"] = 0
    return fig


@callback(
    Output("image-viewer", "figure"),
    Output("image-viewfinder", "figure"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-metadata", "data"),
    Output("annotated-slices-selector", "value"),
    Output("image-selection-slider", "value", allow_duplicate=True),
    Output("notifications-container", "children", allow_duplicate=True),
    Output("image-viewer-loading", "className"),
    Input("image-selection-slider", "value"),
    Input("show-result-overlay-toggle", "checked"),
    Input("annotated-slices-selector", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    State("annotation-store", "data"),
    State("image-metadata", "data"),
    State("screen-size", "data"),
    State("current-class-selection", "data"),
    State("seg-results-train-store", "data"),
    State("seg-results-inference-store", "data"),
    State("seg-result-opacity-slider", "value"),
    State("image-viewer", "figure"),
    prevent_initial_call=True,
)
def render_image(
    image_idx,
    toggle_seg_result,
    slice_selection,
    all_annotation_class_store,
    project_name,
    annotation_store,
    image_metadata,
    screen_size,
    current_color,
    seg_result_train,
    seg_result_inference,
    opacity,
    fig,
):
    reset_slice_selection = dash.no_update
    update_slider_value = dash.no_update
    notification = dash.no_update
    if ctx.triggered_id == "annotated-slices-selector":
        reset_slice_selection = None
        if image_idx == slice_selection:
            ret_values = [dash.no_update] * 8
            ret_values[4] = reset_slice_selection
            ret_values[7] = "hidden"
            return ret_values
        image_idx = slice_selection
        update_slider_value = slice_selection
        notification = generate_notification(
            f"{ANNOT_NOTIFICATION_MSGS['slice-jump']} {image_idx}",
            "indigo",
            ANNOT_ICONS["jump-to-slice"],
        )

    if image_idx:
        image_idx -= 1  # slider starts at 1, so subtract 1 to get the correct index
        tf = tiled_datasets.get_data_sequence_by_name(project_name)[image_idx]
        if toggle_seg_result:
            # if toggle is true and overlay exists already (2 images in data) this will
            # be handled in hide_show_segmentation_overlay callback
            if (
                len(fig["data"]) == 2
                and ctx.triggered_id == "show-result-overlay-toggle"
            ):
                return [dash.no_update] * 7 + ["hidden"]
            # Check if the stored results are for the current project and image
            if seg_result_train or seg_result_inference:
                seg_result = (
                    seg_result_inference if seg_result_inference else seg_result_train
                )
                if "mask_idx" in seg_result and seg_result["mask_idx"] is not None:
                    annotation_indices = seg_result["mask_idx"]
                    if str(image_idx) in annotation_indices:
                        # Will not return an error since we already checked if image_idx is in the list
                        mapped_index = annotation_indices.index(str(image_idx))
                        result = tiled_results.get_data_by_trimmed_uri(
                            seg_result["seg_result_trimmed_uri"], slice=mapped_index
                        )
                    else:
                        result = None
                else:
                    result = tiled_results.get_data_by_trimmed_uri(
                        seg_result["seg_result_trimmed_uri"], slice=image_idx
                    )
            else:
                result = None
    else:
        tf = np.zeros((500, 500))
    fig = px.imshow(tf, binary_string=True)
    if toggle_seg_result and result is not None:
        colorscale, max_class_id = generate_segmentation_colormap(
            all_annotation_class_store
        )
        fig.add_trace(
            go.Heatmap(
                z=result,
                zmin=-0.5,
                zmax=max_class_id + 0.5,
                colorscale=colorscale,
                showscale=False,
            )
        )
        fig["data"][1]["opacity"] = opacity / 100

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        dragmode="drawclosedpath",
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

    if screen_size:
        if view:
            image_center_coor = annotation_store["image_center_coor"]
            # we have a zoom + window size to take into account
            if "xaxis_range_0" in view:
                fig.update_layout(
                    xaxis=dict(range=[view["xaxis_range_0"], view["xaxis_range_1"]]),
                    yaxis=dict(range=[view["yaxis_range_0"], view["yaxis_range_1"]]),
                )
        else:
            # no zoom level to take into account, window size only
            fig, image_center_coor = resize_canvas(
                tf.shape[0], tf.shape[1], screen_size["H"], screen_size["W"], fig
            )

    patched_annotation_store = Patch()
    patched_annotation_store["image_center_coor"] = image_center_coor
    patched_annotation_store["active_img_shape"] = list(tf.shape)

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
        curr_image_metadata,
        reset_slice_selection,
        update_slider_value,
        notification,
        "hidden",
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
            title = "No more images to the left"
            new_slice = dash.no_update
            icon = ANNOT_ICONS["no-more-slices"]
        else:
            new_slice = current_slice - 1
            title = f"{ANNOT_NOTIFICATION_MSGS['slice-left']} ({new_slice}) selected"
            icon = ANNOT_ICONS["slice-left"]
    elif pressed_key == KEYBINDS["slice-right"]:
        if current_slice == max_slice:
            title = "No more images to the right"
            new_slice = dash.no_update
            icon = ANNOT_ICONS["no-more-slices"]
        else:
            new_slice = current_slice + 1
            title = f"{ANNOT_NOTIFICATION_MSGS['slice-right']} ({new_slice}) selected"
            icon = ANNOT_ICONS["slice-right"]
    notification = generate_notification(title, None, icon)

    return new_slice, notification


@callback(
    Output("image-viewfinder", "className", allow_duplicate=True),
    Input("toggle-viewfinder", "checked"),
    prevent_initial_call=True,
)
def toggle_viewdinfer(viewfinder_enabled):
    if viewfinder_enabled:
        return "visible"
    return "hidden"


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
    # Callback is triggered when the image is first loaded, but the annotation_store is not yet populated
    # so we need to prevent the update
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
    function EnableImageLoadingOverlay(a) {
        const ctx = window.dash_clientside.callback_context;
        console.log(ctx)
        if (a == null){return "hidden"}
        return "visible";
    }
    """,
    Output("image-viewer-loading", "className", allow_duplicate=True),
    Input("image-selection-slider", "value"),
    prevent_initial_call=True,
)
clientside_callback(
    """
    function EnableImageLoadingOverlay(a) {
        if (a == null){return "hidden"}
        return "visible";
    }
    """,
    Output("image-viewer-loading", "className", allow_duplicate=True),
    Input("show-result-overlay-toggle", "checked"),
    prevent_initial_call=True,
)
clientside_callback(
    """
    function EnableImageLoadingOverlay(a) {
        if (a == null){return "hidden"}
        return "visible";
    }
    """,
    Output("image-viewer-loading", "className", allow_duplicate=True),
    Input("annotated-slices-selector", "value"),
    prevent_initial_call=True,
)
clientside_callback(
    """
    function EnableImageLoadingOverlay(a) {
        if (a == null){return "hidden"}
        return "visible";
    }
    """,
    Output("image-viewer-loading", "className", allow_duplicate=True),
    Input("project-name-src", "value"),
    prevent_initial_call=True,
)
clientside_callback(
    """
    function DisableImageLoadingOverlay(fig) {
        return "hidden";
    }
    """,
    Output("image-viewer-loading", "className", allow_duplicate=True),
    Input("image-viewer", "figure"),
    prevent_initial_call=True,
)


@callback(
    Output(
        {"type": "annotation-class-store", "index": ALL}, "data", allow_duplicate=True
    ),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("image-viewer", "relayoutData"),
    State("image-selection-slider", "value"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("image-viewer", "figure"),
    prevent_initial_call=True,
)
def locally_store_annotations(
    relayout_data, img_idx, annotation_store, all_annotation_class_store, fig
):
    """
    Upon finishing a relayout event (drawing, modifying, panning or zooming), this function takes the
    currently drawn shapes or zoom/pan data, and stores the lastest added shape to the
    appropriate class-annotation-store, or the image pan/zoom position to the anntations-store.
    """
    img_idx = str(img_idx - 1)
    shapes = []
    # Case 1: panning/zooming, no need to update all the class annotation stores
    if "xaxis.range[0]" in relayout_data:
        annotation_store["view"]["xaxis_range_0"] = relayout_data["xaxis.range[0]"]
        annotation_store["view"]["xaxis_range_1"] = relayout_data["xaxis.range[1]"]
        annotation_store["view"]["yaxis_range_0"] = relayout_data["yaxis.range[0]"]
        annotation_store["view"]["yaxis_range_1"] = relayout_data["yaxis.range[1]"]
        return all_annotation_class_store, annotation_store, dash.no_update
    # Case 2: A shape is modified, drawn or deleted. Save all the current shapes on the fig layout, which includes new
    # modified, and deleted shapes.
    if (
        any(["shapes" in key for key in relayout_data])
        and "shapes" in fig["layout"].keys()
    ):
        shapes = fig["layout"]["shapes"]

    # Clear all annotation from the stores at the current slice,
    # except for the hidden shapes (hidden shapes cannot be modified or deleted)
    for a_class in all_annotation_class_store:
        if not a_class["is_visible"]:
            continue
        if img_idx in a_class["annotations"]:
            del a_class["annotations"][img_idx]
    # Add back each annotation on the current slice in each respective store.
    for shape in shapes:
        for a_class in all_annotation_class_store:
            if a_class["color"] == shape["line"]["color"]:
                if img_idx in a_class["annotations"]:
                    a_class["annotations"][img_idx].append(shape)
                else:
                    a_class["annotations"][img_idx] = [shape]
                break
    # redraw all annotations on the fig so the store is aligned with whats on the app
    # ie: drawing with a hidden class hides the shape immediately
    # ie: drawing with the first class pushes the shape to the back of the image imdediately
    fig = Patch()
    all_annotations = []
    for a in all_annotation_class_store:
        if a["is_visible"] and "annotations" in a and img_idx in a["annotations"]:
            all_annotations += a["annotations"][img_idx]
    fig["layout"]["shapes"] = all_annotations
    return all_annotation_class_store, annotation_store, fig


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
    data_shape = (
        tiled_datasets.get_data_shape_by_name(project_name) if project_name else None
    )
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


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("image-viewer", "relayoutData"),
    Input("reset-view", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def reset_figure_view(n_clicks, annotation_store):
    """
    This callback will reset the view of the image to the center of the screen (no zoom, no pan).
    RelayoutData is updated too, which then triggers callback that updates viewfinder box
    """
    image_center_coor = annotation_store["image_center_coor"]
    if image_center_coor is None:
        raise PreventUpdate

    new_figure = Patch()
    new_figure["layout"]["yaxis"]["range"] = [
        image_center_coor["y1"],
        image_center_coor["y0"],
    ]
    new_figure["layout"]["xaxis"]["range"] = [
        image_center_coor["x0"],
        image_center_coor["x1"],
    ]

    relayout_data = {
        "xaxis.range[0]": image_center_coor["x0"],
        "yaxis.range[0]": image_center_coor["y1"],
        "xaxis.range[1]": image_center_coor["x1"],
        "yaxis.range[1]": image_center_coor["y0"],
    }
    return new_figure, relayout_data
