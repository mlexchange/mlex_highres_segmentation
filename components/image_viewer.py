from dash import html, dcc
import dash_mantine_components as dmc

COMPONENT_STYLE = {
    "width": "640px",
    "height": "calc(100vh - 40px)",
    "padding": "10px",
    "borderRadius": "5px",
    "border": "1px solid rgb(222, 226, 230)",
    "overflowY": "scroll",
}


def layout():
    return html.Div(
        children=[
            dcc.Graph(id="image-viewer", config={"scrollZoom": True}),
            dmc.Space(h=20),
            dmc.Slider(min=1, max=1000, step=1, value=25),
        ],
        style=COMPONENT_STYLE,
    )
