from dash import Dash
import dash_mantine_components as dmc
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout
from callbacks.image_viewer import *
from callbacks.control_bar import *

app = Dash(__name__)
server = app.server

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Group(
            children=[
                control_bar_layout(),
                image_viewer_layout(),
            ],
            position='center'
        )
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
