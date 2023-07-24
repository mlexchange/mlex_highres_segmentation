from dash import Input, Output, State, callback, ctx, Patch, clientside_callback
import dash
import dash_mantine_components as dmc
from tifffile import imread
import plotly.express as px
import numpy as np
from utils.data_utils import convert_hex_to_rgba, data


@callback(
    Output("image-viewer", "figure"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer-loading", "zIndex", allow_duplicate=True),
    Output("data-selection-controls", "children", allow_duplicate=True),
    Output("image-transformation-controls", "children", allow_duplicate=True),
    Output("annotations-controls", "children", allow_duplicate=True),
    Input("image-selection-slider", "value"),
    State("project-name-src", "value"),
    State("paintbrush-width", "value"),
    State("annotation-class-selection", "className"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def render_image(
    image_idx,
    project_name,
    annotation_width,
    annotation_color,
    annotation_store,
):
    if image_idx:
        image_idx -= 1  # slider starts at 1, so subtract 1 to get the correct index
        tf = data[project_name][image_idx]
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
    hex_color = dmc.theme.DEFAULT_COLORS[annotation_color][7]
    fig.update_layout(
        newshape=dict(
            line=dict(
                color=convert_hex_to_rgba(hex_color, 0.3), width=annotation_width
            ),
            fillcolor=convert_hex_to_rgba(hex_color, 0.3),
        )
    )
    if annotation_store:
        if not annotation_store["visible"]:
            fig["layout"]["shapes"] = []
            fig["layout"]["dragmode"] = False
            return fig

        fig["layout"]["dragmode"] = annotation_store["dragmode"]

        if str(image_idx) in annotation_store["annotations"]:
            fig["layout"]["shapes"] = annotation_store["annotations"][str(image_idx)]

        view = annotation_store["view"]
        if "xaxis_range_0" in view and annotation_store["image_size"] == tf.size:
            fig.update_layout(
                xaxis=dict(range=[view["xaxis_range_0"], view["xaxis_range_1"]]),
                yaxis=dict(range=[view["yaxis_range_0"], view["yaxis_range_1"]]),
            )
    patched_annotation_store = Patch()
    patched_annotation_store["image_size"] = tf.size
    fig_loading_overlay = -1

    # No update is needed for the 'children' of the control components
    # since we just want to trigger the loading overlay with this callback
    return (
        fig,
        patched_annotation_store,
        fig_loading_overlay,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


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

    disable_slider = project_name is None
    if not disable_slider:
        tiff_file = data[project_name]
    min_slider_value = 0 if disable_slider else 1
    max_slider_value = 0 if disable_slider else len(tiff_file)
    slider_value = 0 if disable_slider else 1
    annotation_store["annotations"] = {}
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

    return (
        new_slider_value,
        disable_previous_image,
        disable_next_image,
        f"Selected image: {new_slider_value}",
    )
