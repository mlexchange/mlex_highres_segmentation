from dash import Input, Output, callback, Patch, MATCH, ALL, ctx
import dash_mantine_components as dmc
import json


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
    print(width_value)
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["line"]["width"] = 11
    return patched_figure


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input({"type": "annotation-color", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def annotation_color(color_value):
    color = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
    hex_color = dmc.theme.DEFAULT_COLORS[color][7]
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["line"]["color"] = hex_color
    return patched_figure
