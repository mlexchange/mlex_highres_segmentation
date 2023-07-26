from dash import callback, Input, Output, State, no_update
from utils.annotations import Annotations


@callback(
    Output("output-placeholder", "children"),
    Input("run-model", "n_clicks"),
    State("annotation-store", "data"),
)
def run_model(n_clicks, annotation_store):
    if n_clicks:
        return "Running the model..."
    return no_update
