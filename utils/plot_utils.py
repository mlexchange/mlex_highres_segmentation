import plotly.graph_objects as go
import plotly.express as px
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
        x0_original, y0_original, x1_original, y1_original: coordinates of the pan+zoom box in the original image - obtained from relayoutData
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


def create_viewfinder(image_data, downscaled_image_shape):
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
        origin="lower",
    )

    """
    view = annotation_store["view"]
    if "xaxis_range_0" in view:
        x0, y0, x1, y1 = downscale_view(
            view["xaxis_range_0"],
            view["yaxis_range_1"],
            view["xaxis_range_1"],
            view["yaxis_range_0"],
            image_data.shape,
            (img_max_height, img_max_width),
        )
    else:
        x0 = 0
        y0 = img_max_height
        x1 = img_max_width
        y1 = 0
    """

    x0 = 0
    y0 = 0
    x1 = img_max_width
    y1 = img_max_height

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


def get_viewfinder_style(image_ratio):
    if image_ratio < 1:
        return (
            {
                "width": f"calc(10vh/{image_ratio})",
                "height": f"10vh",
                "position": "absolute",
                "top": "30px",
                "right": "0px",
            },
        )
    else:
        return (
            {
                "width": "10vh",
                "height": f"calc(10vh/{image_ratio})",
                "position": "absolute",
                "top": "30px",
                "right": "0px",
            },
        )


def get_view_finder_max_min(image_ratio):
    if image_ratio < 1:
        return 250, 250 * image_ratio
    else:
        return 250 / image_ratio, 250
