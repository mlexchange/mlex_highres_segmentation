import asyncio
import os
import traceback
import uuid
from datetime import datetime

import pytz
from dash import ALL, Input, Output, State, callback, no_update

from constants import ANNOT_ICONS
from utils.data_utils import tiled_dataset
from utils.plot_utils import generate_notification
from utils.prefect import get_flow_run_name, query_flow_run, schedule_prefect_flow

MODE = os.getenv("MODE", "")
RESULTS_DIR = os.getenv("RESULTS_DIR", "")
FLOW_NAME = os.getenv("FLOW_NAME", "")
PREFECT_TAGS = os.getenv("PREFECT_TAGS", ["high-res-segmentation"])

# TODO: Retrieve timezone from browser
TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")

# TODO: Get model parameters from UI
TRAIN_PARAMS_EXAMPLE = {
    "flow_type": "podman",
    "params_list": [
        {
            "image_name": "ghcr.io/mlexchange/mlex_dlsia_segmentation_prototype",
            "image_tag": "main",
            "command": 'python -c \\"import time; time.sleep(30)\\"',
            "params": {"test": "test"},
            "volumes": [f"{RESULTS_DIR}:/app/work/results"],
        },
        {
            "image_name": "ghcr.io/mlexchange/mlex_dlsia_segmentation_prototype",
            "image_tag": "main",
            "command": 'python -c \\"import time; time.sleep(10)\\"',
            "params": {"test": "test"},
            "volumes": [f"{RESULTS_DIR}:/app/work/results"],
        },
    ],
}

INFERENCE_PARAMS_EXAMPLE = {
    "flow_type": "podman",
    "params_list": [
        {
            "image_name": "ghcr.io/mlexchange/mlex_dlsia_segmentation_prototype",
            "image_tag": "main",
            "command": 'python -c \\"import time; time.sleep(30)\\"',
            "params": {"test": "test"},
            "volumes": [f"{RESULTS_DIR}:/app/work/results"],
        },
    ],
}


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Input("run-train", "n_clicks"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    State("job-name", "value"),
    prevent_initial_call=True,
)
def run_train(n_clicks, global_store, all_annotations, project_name, job_name):
    """
    This callback collects parameters from the UI and submits a training job to Prefect.
    If the app is run from "dev" mode, then only a placeholder job_uid will be created.

    # TODO: Appropriately paramaterize the job json depending on user inputs
    and relevant file paths
    """
    if n_clicks:
        if MODE == "dev":
            job_uid = str(uuid.uuid4())
            job_message = f"Job has been succesfully submitted with uid: {job_uid}"
            notification_color = "indigo"
        else:
            tiled_dataset.save_annotations_data(
                global_store, all_annotations, project_name
            )
            try:
                # Schedule job
                current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime(
                    "%Y/%m/%d %H:%M:%S"
                )
                job_uid = schedule_prefect_flow(
                    FLOW_NAME,
                    parameters=TRAIN_PARAMS_EXAMPLE,
                    flow_run_name=f"{job_name} {current_time}",
                    tags=PREFECT_TAGS + ["train"],
                )
                job_message = f"Job has been succesfully submitted with uid: {job_uid}"
                notification_color = "indigo"
            except Exception as e:
                # Print the traceback to the console
                traceback.print_exc()
                job_uid = None
                job_message = f"Job presented error: {e}"
                notification_color = "red"

        notification = generate_notification(
            "Job Submission", notification_color, ANNOT_ICONS["submit"], job_message
        )

        return notification
    return no_update


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Input("run-inference", "n_clicks"),
    State("train-job-selector", "value"),
    prevent_initial_call=True,
)
def run_inference(n_clicks, train_job_id):
    """
    This callback collects parameters from the UI and submits an inference job to Prefect.
    If the app is run from "dev" mode, then only a placeholder job_uid will be created.

    # TODO: Appropriately paramaterize the job json depending on user inputs
    and relevant file paths
    """
    if n_clicks:
        if MODE == "dev":
            job_uid = str(uuid.uuid4())
            job_message = f"Job has been succesfully submitted with uid: {job_uid}"
            notification_color = "indigo"
        else:
            if train_job_id is not None:
                job_name = get_flow_run_name(train_job_id)
                if job_name is not None:
                    try:
                        # Schedule job
                        current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime(
                            "%Y/%m/%d %H:%M:%S"
                        )
                        job_uid = schedule_prefect_flow(
                            FLOW_NAME,
                            parameters=INFERENCE_PARAMS_EXAMPLE,
                            flow_run_name=f"{job_name} {current_time}",
                            tags=PREFECT_TAGS + ["inference"],
                        )
                        job_message = (
                            f"Job has been succesfully submitted with uid: {job_uid}"
                        )
                        notification_color = "indigo"
                    except Exception as e:
                        # Print the traceback to the console
                        traceback.print_exc()
                        job_uid = None
                        job_message = f"Job presented error: {e}"
                else:
                    job_message = "Please select a valid train job"
                    notification_color = "red"
            else:
                job_message = "Please select a train job from the dropdown"
                notification_color = "red"

        notification = generate_notification(
            "Job Submission", notification_color, ANNOT_ICONS["submit"], job_message
        )

        return notification

    return no_update


@callback(
    Output("train-job-selector", "data"),
    Input("model-check", "n_intervals"),
)
def check_train_job(n_intervals):
    """
    This callback populates the train job selector dropdown with job names and ids from Prefect.
    This callback displays the current status of the job as part of the job name in the dropdown.
    In "dev" mode, the dropdown is populated with the sample data below.
    """
    if MODE == "dev":
        data = [
            {"label": "❌ DLSIA ABC 03/11/2024 15:38PM", "value": "uid0001"},
            {"label": "🕑 DLSIA XYC 03/11/2024 14:21PM", "value": "uid0002"},
            {"label": "✅ DLSIA CBA 03/11/2024 10:02AM", "value": "uid0003"},
        ]
    else:
        data = asyncio.run(query_flow_run(PREFECT_TAGS + ["train"]))
    return data


@callback(
    Output("inference-job-selector", "data"),
    Output("inference-job-selector", "value"),
    Input("model-check", "n_intervals"),
    Input("train-job-selector", "value"),
)
def check_inference_job(n_intervals, train_job_id):
    """
    This callback populates the inference job selector dropdown with job names and ids from Prefect.
    The list of jobs is filtered by the selected train job in the train job selector dropdown.
    The selected value is set to None if the list of jobs is empty.
    This callback displays the current status of the job as part of the job name in the dropdown.
    In "dev" mode, the dropdown is populated with the sample data below.
    """
    if MODE == "dev":
        data = [
            {"label": "❌ DLSIA ABC 03/11/2024 15:38PM", "value": "uid0001"},
            {"label": "🕑 DLSIA XYC 03/11/2024 14:21PM", "value": "uid0002"},
            {"label": "✅ DLSIA CBA 03/11/2024 10:02AM", "value": "uid0003"},
        ]
        return data, None
    else:
        if train_job_id is not None:
            job_name = get_flow_run_name(train_job_id)
            if job_name is not None:
                if MODE == "dev":
                    data = [
                        {
                            "label": "❌ DLSIA ABC 03/11/2024 15:38PM",
                            "value": "uid0001",
                        },
                        {
                            "label": "🕑 DLSIA XYC 03/11/2024 14:21PM",
                            "value": "uid0002",
                        },
                        {
                            "label": "✅ DLSIA CBA 03/11/2024 10:02AM",
                            "value": "uid0003",
                        },
                    ]
                else:
                    data = asyncio.run(
                        query_flow_run(
                            PREFECT_TAGS + ["inference"], flow_run_name=job_name
                        )
                    )
                    selected_value = None if len(data) == 0 else no_update
                return data, selected_value
        return [], None
