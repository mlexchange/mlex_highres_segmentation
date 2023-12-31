import os

import dash_auth
import dash_mantine_components as dmc
from dash import Dash, dcc

from callbacks.control_bar import *
from callbacks.image_viewer import *
from callbacks.segmentation import *
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout

USER_NAME = os.getenv("USER_NAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")

VALID_USER_NAME_PASSWORD_PAIRS = {USER_NAME: USER_PASSWORD}

app = Dash(__name__, update_title=None)
server = app.server

# Set single user name password pair if deployment isn't
auth = (
    dash_auth.BasicAuth(app, VALID_USER_NAME_PASSWORD_PAIRS)
    if os.getenv("DASH_DEPLOYMENT_LOC", "") != "Local"
    else None
)

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
