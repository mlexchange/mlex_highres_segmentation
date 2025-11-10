import os
from datetime import datetime

import pytz
from dash import Input, Output, callback, no_update

from components.control_bar import create_infra_state_details
from utils.data_utils import tiled_datasets, tiled_masks, tiled_results
from utils.plot_utils import generate_notification
from utils.prefect import check_prefect_ready, check_prefect_worker_ready
from utils.mlflow_utils import MLflowClient

TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")
FLOW_NAME = os.getenv("FLOW_NAME", "")


@callback(
    Output("infra-state", "data", allow_duplicate=True),
    Input("infra-check", "n_intervals"),
    prevent_initial_call="initial_dupulicate",
)
def check_infra_state(n_intervals):
    infra_state = {}

    current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime("%Y/%m/%d %H:%M:%S")
    infra_state["last_checked"] = current_time

    any_infra_down = False

    # Tiled: Check if data, masks, and results are reachable (from_uri did not raise an exception)
    tiled_data_ready = tiled_datasets.check_dataloader_ready()
    infra_state["tiled_data_ready"] = tiled_data_ready
    if not tiled_data_ready:
        any_infra_down = True
    tiled_masks_ready = tiled_masks.check_mask_handler_ready()
    infra_state["tiled_masks_ready"] = tiled_masks_ready
    if not tiled_masks_ready:
        any_infra_down = True
    # The segmentation application will make sure that all containers that are needed exist
    tiled_results_ready = tiled_results.check_dataloader_ready(base_uri_only=True)
    infra_state["tiled_results_ready"] = tiled_results_ready
    if not tiled_results_ready:
        any_infra_down = True

    # Prefect: Check prefect API is reachable, and the worker is ready (flow is deployed and ready)
    try:
        check_prefect_ready()
        infra_state["prefect_ready"] = True
    except Exception:
        any_infra_down = True
        infra_state["prefect_ready"] = False
    try:
        check_prefect_worker_ready(FLOW_NAME)
        infra_state["prefect_worker_ready"] = True
    except Exception:
        any_infra_down = True
        infra_state["prefect_worker_ready"] = False
    
    # MLFLOW: Check MLFlow is reachable
    try:
        mlflow_client = MLflowClient()
        infra_state["mlflow_ready"] = mlflow_client.check_mlflow_ready()
        if not infra_state["mlflow_ready"]:
            any_infra_down = True
    except Exception:
        any_infra_down = True
        infra_state["mlflow_ready"] = False
    
    if any_infra_down:
        infra_state["any_infra_down"] = True
    else:
        infra_state["any_infra_down"] = False
    return infra_state


@callback(
    Output("infra-state-icon", "icon"),
    Output("infra-state-summary", "color"),
    Output("infra-state-details", "children"),
    Output("notifications-container", "children", allow_duplicate=True),
    Input("infra-state", "data"),
    prevent_initial_call=True,
)
def update_infra_state(infra_state):

    if infra_state is None:
        return no_update, no_update, no_update, no_update

    any_infra_down = infra_state["any_infra_down"]
    last_checked = f"{infra_state['last_checked']}"

    infra_details = create_infra_state_details(
        tiled_data_ready=infra_state["tiled_data_ready"],
        tiled_masks_ready=infra_state["tiled_masks_ready"],
        tiled_results_ready=infra_state["tiled_results_ready"],
        prefect_ready=infra_state["prefect_ready"],
        prefect_worker_ready=infra_state["prefect_worker_ready"],
        mlflow_ready=infra_state["mlflow_ready"],
        timestamp=last_checked,
    )

    if any_infra_down:
        notification = generate_notification(
            "Infrastructure State",
            "red",
            "ph:network-x",
            "One or more infrastructure components are not reachable!",
        )
        infra_state_icon = "ph:network-x"
        infra_state_color = "red"
    else:
        notification = no_update
        infra_state_icon = "ph:network-fill"
        infra_state_color = "gray"
    return infra_state_icon, infra_state_color, infra_details, notification
