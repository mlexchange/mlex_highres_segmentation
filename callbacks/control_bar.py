from dash import Input, Output, State, callback, Patch, ALL, ctx, clientside_callback
import dash_mantine_components as dmc
import json
from utils.data_utils import convert_hex_to_rgba, data


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("annotation-opacity", "value"),
    prevent_initial_call=True,
)
def annotation_opacity(opacity_value):
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["opacity"] = opacity_value
    return patched_figure


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
    Output("annotation-class-selection", "className"),
    Input({"type": "annotation-color", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def annotation_color(color_value):
    """
    This callback is responsible for changing the color of the brush.
    """
    color_name = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
    hex_color = dmc.theme.DEFAULT_COLORS[color_name][7]
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = convert_hex_to_rgba(
        hex_color, 0.3
    )
    patched_figure["layout"]["newshape"]["line"]["color"] = hex_color
    return patched_figure, color_name


@callback(
    Output("annotation-store", "data"),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx)

    patched_figure = Patch()
    if checked:
        store["visible"] = True
        patched_figure["layout"]["shapes"] = store[image_idx]
    else:
        annotation_data = (
            [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
        )
        store[image_idx] = annotation_data
        patched_figure["layout"]["shapes"] = []

    return store, patched_figure


clientside_callback(
    """
    function dash_filters_clientside(brightness, contrast) {
    console.log(brightness, contrast)
        js_path = "#image-viewer > div.js-plotly-plot > div > div > svg:nth-child(1) > g.cartesianlayer > g > g.plot > g"
        changeFilters(js_path, brightness, contrast)
        return ""
    }
    """,
    Output("dummy-output", "children", allow_duplicate=True),
    Input("figure-brightness", "value"),
    Input("figure-contrast", "value"),
    prevent_initial_call=True,
)


@callback(
    Output("figure-brightness", "value", allow_duplicate=True),
    Output("figure-contrast", "value", allow_duplicate=True),
    Input("filters-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(n_clicks):
    default_brightness = 100
    default_contrast = 100
    return default_brightness, default_contrast
