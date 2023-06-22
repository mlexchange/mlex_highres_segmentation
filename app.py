from dash import Dash
import dash_mantine_components as dmc
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout
from callbacks.image_viewer import *

from utils.data_utils import DEV_download_google_sample_data

DEV_download_google_sample_data()

app = Dash(__name__)

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
