import os

import dash_auth
import dash_mantine_components as dmc
from dash import Dash

from callbacks.control_bar import *  # noqa: F403, F401
from callbacks.image_viewer import *  # noqa: F403, F401
from callbacks.segmentation import *  # noqa: F403, F401
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
    ],
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8075, debug=True)
