from dash import (
    Input,
    Output,
    State,
    callback,
    Patch,
    ALL,
    ctx,
    clientside_callback,
)
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import json
from utils.data_utils import convert_hex_to_rgba, data


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("open-freeform", "style"),
    Output("closed-freeform", "style"),
    Output("circle", "style"),
    Output("rectangle", "style"),
    Output("drawing-off", "style"),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("open-freeform", "n_clicks"),
    Input("closed-freeform", "n_clicks"),
    Input("circle", "n_clicks"),
    Input("rectangle", "n_clicks"),
    Input("drawing-off", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def annotation_mode(open, closed, circle, rect, off_mode, annotation_store):
    """This callback determines which drawing mode the graph is in"""
    if not annotation_store["visible"]:
        raise PreventUpdate

    patched_figure = Patch()
    triggered = ctx.triggered_id
    open_style = {"border": "1px solid"}
    close_style = {"border": "1px solid"}
    circle_style = {"border": "1px solid"}
    rect_style = {"border": "1px solid"}
    pan_style = {"border": "1px solid"}

    if triggered == "open-freeform" and open > 0:
        patched_figure["layout"]["dragmode"] = "drawopenpath"
        annotation_store["dragmode"] = "drawopenpath"
        open_style = {"border": "3px solid black"}
    if triggered == "closed-freeform" and closed > 0:
        patched_figure["layout"]["dragmode"] = "drawclosedpath"
        annotation_store["dragmode"] = "drawclosedpath"
        close_style = {"border": "3px solid black"}
    if triggered == "circle" and circle > 0:
        patched_figure["layout"]["dragmode"] = "drawcircle"
        annotation_store["dragmode"] = "drawcircle"
        circle_style = {"border": "3px solid black"}
    if triggered == "rectangle" and rect > 0:
        patched_figure["layout"]["dragmode"] = "drawrect"
        annotation_store["dragmode"] = "drawrect"
        rect_style = {"border": "3px solid black"}
    if triggered == "drawing-off" and off_mode > 0:
        patched_figure["layout"]["dragmode"] = "pan"
        annotation_store["dragmode"] = "pan"
        pan_style = {"border": "3px solid black"}
    return (
        patched_figure,
        open_style,
        close_style,
        circle_style,
        rect_style,
        pan_style,
        annotation_store,
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
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, annotation_store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx - 1)
    patched_figure = Patch()
    if checked:
        annotation_store["visible"] = True
        patched_figure["layout"]["visible"] = True
        if str(image_idx) in annotation_store["annotations"]:
            patched_figure["layout"]["shapes"] = annotation_store["annotations"][
                image_idx
            ]
        patched_figure["layout"]["dragmode"] = annotation_store["dragmode"]
    else:
        new_annotation_data = (
            [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
        )
        annotation_store["visible"] = False
        patched_figure["layout"]["dragmode"] = False
        annotation_store["annotations"][image_idx] = new_annotation_data
        patched_figure["layout"]["shapes"] = []

    return annotation_store, patched_figure


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
