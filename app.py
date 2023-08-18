from dash import Dash, dcc, clientside_callback, ClientsideFunction
import dash_mantine_components as dmc
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout
from callbacks.image_viewer import *
from callbacks.control_bar import *
from callbacks.segmentation import *

app = Dash(__name__)
server = app.server

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        control_bar_layout(),
        image_viewer_layout(),
        dcc.Store(id="current-ann-mode"),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
