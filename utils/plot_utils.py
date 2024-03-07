import random

import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash_iconify import DashIconify
from skimage.transform import resize


def blank_fig():
    """
    Creates a blank figure with no axes, grid, or background.
    """
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


def downscale_view(
    x0_original,
    y0_original,
    x1_original,
    y1_original,
    active_image_size,
    downscaled_image_size,
):
    """
    This function takes pan+zoom location in the original image and downscales it relatively to viewfinder's lower resolution.
    params:
        x0_original, y0_original, x1_original, y1_original: coordinates of the pan+zoom box in the original image
            - obtained from relayoutData
        active_image_size: size of the original image (height, width) in pixels
        downscaled_image_size: size of the viewfinder (height, width) in pixels
    returns:
        x0, y0, x1, y1: coordinates of the downscaled pan+zoom box in the viewfinder
    """
    max_height, max_width = downscaled_image_size
    original_height, original_width = active_image_size
    scaling_factor_height = original_height / max_height
    scaling_factor_width = original_width / max_width
    inverse_scaling_factor_height = 1.0 / scaling_factor_height
    inverse_scaling_factor_width = 1.0 / scaling_factor_width

    x0 = x0_original * inverse_scaling_factor_width
    y0 = y0_original * inverse_scaling_factor_height
    x1 = x1_original * inverse_scaling_factor_width
    y1 = y1_original * inverse_scaling_factor_height
    return x0, y0, x1, y1


def create_viewfinder(image_data, downscaled_image_shape, view):
    """
    Creates a viewfinder for the image viewer. The viewfinder is a small box that shows the current view of the image
    in the image viewer. It is used to quickly navigate to different parts of the image.
    The image viewer is a downscaled to `downscaled_image_shape` version of the original image.
    """
    img_max_height, img_max_width = downscaled_image_shape
    img_resized = resize(image_data, (img_max_height, img_max_width))

    # Create the downscale image
    fig = px.imshow(
        img_resized,
        binary_string=True,
        width=img_max_width,
        height=img_max_height,
    )

    x0 = 0
    y0 = 0
    x1 = img_max_width
    y1 = img_max_height

    if view:
        if "xaxis_range_0" in view:
            x0, y0, x1, y1 = downscale_view(
                view["xaxis_range_0"],
                view["yaxis_range_0"],
                view["xaxis_range_1"],
                view["yaxis_range_1"],
                image_data.shape,
                (img_max_height, img_max_width),
            )
            x0 = x0 if x0 > 0 else 0
            y0 = y0 if y0 < img_max_height else img_max_height
            x1 = x1 if x1 < img_max_width else img_max_width
            y1 = y1 if y1 > 0 else 0

    # Create the viewfinder box
    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        line=dict(color="red", width=5),
    )

    # Update the layout to any remove other elements other than image and box
    fig.update_layout(
        xaxis=dict(
            showline=False,
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            showline=False,
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        title="",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode=False,
    )
    return fig


def get_view_finder_max_min(image_ratio):
    if image_ratio < 1:
        return 250, 250 * image_ratio
    else:
        return 250 / image_ratio, 250


def resize_canvas(h, w, H, W, figure):
    img_ratio = w / h
    screen_ratio = W / H
    if w <= W and h <= H:
        x1 = W - (W - w) / 2
        x0 = -(W - w) / 2
        y1 = H - (H - h) / 2
        y0 = -(H - h) / 2
    elif w > W:
        if img_ratio <= screen_ratio:
            x1 = h * screen_ratio - h * (screen_ratio - img_ratio) / 2
            x0 = -h * (screen_ratio - img_ratio) / 2
            y1 = h
            y0 = 0
        else:
            x1 = w
            x0 = 0
            y1 = w / screen_ratio - w * (1 / screen_ratio - 1 / img_ratio) / 2
            y0 = -w * (1 / screen_ratio - 1 / img_ratio) / 2

    elif w < W and h > H:
        if w >= h:
            x1 = w * (screen_ratio / img_ratio) - h * (screen_ratio - img_ratio) / 2
            x0 = 0 - h * (screen_ratio - img_ratio) / 2
            y1 = h
            y0 = 0
        else:
            x1 = w * (screen_ratio / img_ratio) - h * (screen_ratio - img_ratio) / 2
            x0 = 0 - h * (screen_ratio - img_ratio) / 2
            y1 = h
            y0 = 0

    figure.update_yaxes(range=[y1, y0])
    figure.update_xaxes(range=[x0, x1])

    image_center_coor = {"y1": y1, "y0": y0, "x0": x0, "x1": x1}
    return figure, image_center_coor


def generate_segmentation_colormap(all_annotations_data):
    """
    Generates a discrete colormap for the segmentation overlay
    based on the color information per class.

    The discrete colormap maps values from 0 to 1 to colors,
    but is meant to be applied to images with class ids as values,
    with these varying from 0 to the number of classes - 1.
    To account for numerical inaccuracies, it is best to center the plot range
    around the class ids, by setting cmin=-0.5 and cmax=max_class_id+0.5.
    """
    max_class_id = max(
        [annotation_class["class_id"] for annotation_class in all_annotations_data]
    )
    # heatmap requires a normalized range from 0 to 1
    # We need to specify color for at least the range limits (0 and 1)
    # as well for every additional class
    # due to using zero-based class ids, we need to add 2 to the max class id
    normalized_range = np.linspace(0, 1, max_class_id + 2)
    color_list = [
        annotation_class["color"] for annotation_class in all_annotations_data
    ]
    # We need to repeat each color twice, to create discrete color segments
    # This loop contains the range limits 0 and 1 once,
    # but every other value in between twice
    colorscale = [
        [normalized_range[i + j], color_list[i % len(color_list)]]
        for i in range(0, normalized_range.size - 1)
        for j in range(2)
    ]
    return colorscale, max_class_id


def generate_notification(title, color, icon, message=""):
    return dmc.Notification(
        title=title,
        message=message,
        color=color,
        icon=DashIconify(icon=icon, width=40),
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        styles={"icon": {"height": "50px", "width": "50px"}},
    )


def generate_notification_bg_icon_col(title, color, icon, message=""):
    """
    This function generates a notification with a background color and an icon and changes icon color too.
    """
    return dmc.Notification(
        title=title,
        message=message,
        icon=DashIconify(icon=icon, width=40),
        id=f"notification-{random.randint(0, 10000)}",
        action="show",
        styles={
            "icon": {
                "height": "50px",
                "width": "50px",
                "backgroundColor": f"{color} !important",
            }
        },
    )
