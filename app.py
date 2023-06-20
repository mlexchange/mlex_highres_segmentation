import dash
from dash import html
import dash_mantine_components as dmc
from components.control_bar import layout as cb_layout
from components.image_viewer import layout as iv_layout
from callbacks import image_viewer


app = dash.Dash(__name__)

app.layout = dmc.Group([html.Div(cb_layout()), html.Div(iv_layout())])

if __name__ == "__main__":
    app.run_server(debug=True)
