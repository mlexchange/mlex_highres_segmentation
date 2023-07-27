from dash import Dash
import dash_mantine_components as dmc
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout
from callbacks.image_viewer import *
from callbacks.control_bar import *

import os
import dash_auth

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    USERNAME: PASSWORD
}


app = Dash(__name__)
server = app.server

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Group(
            children=[
                control_bar_layout(),
                image_viewer_layout(),
            ],
        )
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
