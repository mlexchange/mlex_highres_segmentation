import dash_mantine_components as dmc
from dash import Dash, dcc

from callbacks.control_bar import *
from callbacks.image_viewer import *
from callbacks.segmentation import *
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout

app = Dash(__name__)
server = app.server

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        control_bar_layout(),
        image_viewer_layout(),
        dcc.Store(id="current-class-selection", data="#FFA200"),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
