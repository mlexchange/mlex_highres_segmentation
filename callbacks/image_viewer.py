from dash import Input, Output, State, callback, ctx
import dash_mantine_components as dmc
from tifffile import imread
import plotly.express as px
import numpy as np
from utils import data_utils
from utils.data_utils import convert_hex_to_rgba


@callback(
    Output("image-viewer", "figure"),
    Input("image-selection-slider", "value"),
    State("project-data", "data"),
    State("paintbrush-width", "value"),
    State("annotation-opacity", "value"),
    State("annotation-class-selection", "className"),
    State("annotation-store", "data"),
)
def render_image(
    image_idx,
    project_data,
    annotation_width,
    annotation_opacity,
    annotation_color,
    annotation_data,
):
    if image_idx:
        project_name = project_data["project_name"]
        img_idx = (
            image_idx - 1
        )  # slider starts at 1, so subtract 1 to get the correct index
        selected_file = project_data["project_files"][img_idx]
        tf = imread(f"data/{project_name}/{selected_file}")
    else:
        tf = np.zeros((500, 500))
    fig = px.imshow(tf, binary_string=True)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        dragmode="pan",
        height=620,
        width=620,
    )

    # set the default annotation style
    hex_color = dmc.theme.DEFAULT_COLORS[annotation_color][7]
    fig.update_layout(
        newshape=dict(
            line=dict(
                color=convert_hex_to_rgba(hex_color, 0.3), width=annotation_width
            ),
            fillcolor=convert_hex_to_rgba(hex_color, 0.3),
            opacity=annotation_opacity,
        )
    )
    print("here", image_idx, annotation_data)
    if annotation_data:
        print(str(image_idx) in annotation_data)
        if str(image_idx) in annotation_data:
            fig["layout"]["shapes"] = annotation_data[str(image_idx)]
    return fig


@callback(
    Output("annotation-store", "data", allow_duplicate=True),
    Input("image-viewer", "relayoutData"),
    State("image-selection-slider", "value"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def locally_store_annotations(relayout_data, img_idx, annotation_data):
    """
    Upon finishing relayout event (drawing, but it also includes panning, zooming),
    this function takes the annotation shapes, and stores it in the dcc.Store, which is then used elsewhere
    to preserve drawn annotations, or to save them.
    """
    if "shapes" in relayout_data:
        annotation_data[str(img_idx)] = relayout_data["shapes"]
    return annotation_data


@callback(
    Output("image-selection-slider", "min"),
    Output("image-selection-slider", "max"),
    Output("image-selection-slider", "value"),
    Output("image-selection-slider", "disabled"),
    Output("project-data", "data"),
    Input("project-name-src", "value"),
)
def update_slider_values(project_name):
    """
    When the data source is loaded, this callback will set the slider values and chain call
        "update_selection_and_image" callback which will update image and slider selection component

    ## todo - change Input("project-name-src", "data") to value when image-src will contain buckets of data and not just one image
    ## todo - eg, when a different image source is selected, update slider values which is then used to select image within that source
    """
    project_tiff_files = data_utils.get_tiff_files(project_name)

    disable_slider = project_tiff_files is None
    min_slider_value = 0 if disable_slider else 1
    max_slider_value = 0 if disable_slider else len(project_tiff_files)
    slider_value = 0 if disable_slider else 1
    project_data = {
        "project_name": project_name,
        "project_files": project_tiff_files,
    }
    return (
        min_slider_value,
        max_slider_value,
        slider_value,
        disable_slider,
        project_data,
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
