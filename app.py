import os

import dash_auth
import dash_mantine_components as dmc
from dash import Dash, dcc

from callbacks.control_bar import *  # noqa: F403, F401
from callbacks.image_viewer import *  # noqa: F403, F401
from callbacks.segmentation import *  # noqa: F403, F401
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout

from utils.content_registry import models
from components.dash_component_editor import JSONParameterEditor

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
        dcc.Store(id="gui-components-values", data={})
    ],
)

### automatic Dash gui callback ###
@callback(
    Output("gui-layouts", "children"),
    Input("model-list", "value"),
)
def update_gui_parameters(model_name):
    data = models.models[model_name]
    if data["gui_parameters"]:                    
        item_list = JSONParameterEditor( _id={'type': str(uuid.uuid4())}, # pattern match _id (base id), name
                                         json_blob=models.remove_key_from_dict_list(data["gui_parameters"], "comp_group"),
                                        )
        item_list.init_callbacks(app)
        return [html.H4("Model Parameters"), item_list]
    else:
        return[""] 


if __name__ == "__main__":
    app.run_server(debug=True)
