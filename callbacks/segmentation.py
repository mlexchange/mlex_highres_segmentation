import os
import traceback
import uuid
from datetime import datetime

import pytz

from constants import ANNOT_ICONS
from dash import ALL, Input, Output, State, callback, no_update
from utils.data_utils import (
    assemble_io_parameters_from_uris,
    extract_parameters_from_html,
    tiled_datasets,
    tiled_masks,
    tiled_results,
)
from utils.plot_utils import generate_notification
from utils.prefect import (
    get_children_flow_run_ids,
    get_flow_run_name,
    get_flow_runs_by_name,
    schedule_prefect_flow,
)

MODE = os.getenv("MODE", "")
RESULTS_DIR = os.getenv("RESULTS_DIR", "")
FLOW_NAME = os.getenv("FLOW_NAME", "")
PREFECT_TAGS = os.getenv("PREFECT_TAGS", ["high-res-segmentation"])

FLOW_TYPE = os.getenv("FLOW_TYPE", "conda")
TRAIN_SCRIPT_PATH = os.getenv("TRAIN_SCRIPT_PATH", "scr/train.py")
SEGMENT_SCRIPT_PATH = os.getenv("SEGMENT_SCRIPT_PATH", "scr/segment.py")

CONDA_ENV_NAME = os.getenv("CONDA_ENV_NAME", "dlsia")
IMAGE_NAME = os.getenv("DOCKER_IMAGE_NAME", None)
IMAGE_TAG = os.getenv("DOCKER_IMAGE_TAG", None)

# TODO: Retrieve timezone from browser
TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")

# TODO: Get model parameters from UI
if FLOW_TYPE == "podman":
    TRAIN_PARAMS_EXAMPLE = {
        "flow_type": "podman",
        "params_list": [
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {TRAIN_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
        ],
    }

    INFERENCE_PARAMS_EXAMPLE = {
        "flow_type": "podman",
        "params_list": [
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
        ],
    }

elif FLOW_TYPE == "conda":
    TRAIN_PARAMS_EXAMPLE = {
        "flow_type": "conda",
        "params_list": [
            {
                "conda_env_name": f"{CONDA_ENV_NAME}",
                "python_file_name": f"{TRAIN_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
            },
            {
                "conda_env_name": f"{CONDA_ENV_NAME}",
                "python_file_name": f"{SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
            },
        ],
    }

    INFERENCE_PARAMS_EXAMPLE = {
        "flow_type": "conda",
        "params_list": [
            {
                "conda_env_name": f"{CONDA_ENV_NAME}",
                "python_file_name": f"{SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
            },
        ],
    }

else:
    TRAIN_PARAMS_EXAMPLE = {
        "flow_type": "docker",
        "params_list": [
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {TRAIN_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
        ],
    }

    INFERENCE_PARAMS_EXAMPLE = {
        "flow_type": "docker",
        "params_list": [
            {
                "image_name": f"{IMAGE_NAME}",
                "image_tag": f"{IMAGE_TAG}",
                "command": f"python {SEGMENT_SCRIPT_PATH}",
                "params": {
                    "io_parameters": {"uid_save": "uid0001", "uid_retrieve": "uid0001"}
                },
                "volumes": [f"{RESULTS_DIR}:/app/work/results"],
            },
        ],
    }


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Output("model-parameter-values", "data"),
    Input("run-train", "n_clicks"),
    State("annotation-store", "data"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    State("model-parameters", "children"),
    State("model-list", "value"),
    State("job-name", "value"),
    prevent_initial_call=True,
)
def run_train(
    n_clicks,
    global_store,
    all_annotations,
    project_name,
    model_parameter_container,
    model_name,
    job_name,
):
    """
    This callback collects parameters from the UI and submits a training job to Prefect.
    If the app is run from "dev" mode, then only a placeholder job_uid will be created.

    """
    if n_clicks:
        model_parameters, parameter_errors = extract_parameters_from_html(
            model_parameter_container
        )
        # Check if the model parameters are valid
        if parameter_errors:
            notification = generate_notification(
                "Model Parameters",
                "red",
                ANNOT_ICONS["parameters"],
                "Model parameters are not valid!",
            )
            return notification, no_update
        mask_uri, num_classes, mask_error_message = tiled_masks.save_annotations_data(
            global_store, all_annotations, project_name
        )
        model_parameters["num_classes"] = num_classes
        model_parameters["network"] = model_name

        if mask_uri is None:
            notification = generate_notification(
                "Mask Export", "red", ANNOT_ICONS["export"], mask_error_message
            )
            return notification, model_parameters

        # Set io_parameters for both training and partial inference
        # Uid retrieve is set to None because the partial inference job will be
        # populated with the the uid_save of the training job
        # This is handled in the Prefect worker
        current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        flow_run_name = f"{job_name} {current_time}"
        data_uri = tiled_datasets.get_data_uri_by_name(project_name)
        io_parameters = assemble_io_parameters_from_uris(data_uri, mask_uri)
        io_parameters["uid_retrieve"] = ""
        io_parameters["models_dir"] = RESULTS_DIR
        io_parameters["job_name"] = flow_run_name

        TRAIN_PARAMS_EXAMPLE["params_list"][0]["params"][
            "io_parameters"
        ] = io_parameters
        TRAIN_PARAMS_EXAMPLE["params_list"][1]["params"][
            "io_parameters"
        ] = io_parameters
        TRAIN_PARAMS_EXAMPLE["params_list"][0]["params"][
            "model_parameters"
        ] = model_parameters
        TRAIN_PARAMS_EXAMPLE["params_list"][1]["params"][
            "model_parameters"
        ] = model_parameters

        if MODE == "dev":
            job_uid = str(uuid.uuid4())
            job_message = f"Dev Mode: Job has been succesfully submitted with uid: {job_uid} and mask uri: {mask_uri}"
            notification_color = "indigo"
        else:
            try:
                # Schedule job
                job_uid = schedule_prefect_flow(
                    FLOW_NAME,
                    parameters=TRAIN_PARAMS_EXAMPLE,
                    flow_run_name=flow_run_name,
                    tags=PREFECT_TAGS + ["train", project_name],
                )
                job_message = f"Job has been succesfully submitted with uid: {job_uid} and mask uri: {mask_uri}"
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

        return notification, model_parameters
    return no_update, no_update


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Input("run-inference", "n_clicks"),
    State("train-job-selector", "value"),
    State({"type": "annotation-class-store", "index": ALL}, "data"),
    State("project-name-src", "value"),
    State("model-parameters", "children"),
    State("model-list", "value"),
    prevent_initial_call=True,
)
def run_inference(
    n_clicks,
    train_job_id,
    all_annotations,
    project_name,
    model_parameter_container,
    model_name,
):
    """
    This callback collects parameters from the UI and submits an inference job to Prefect.
    If the app is run from "dev" mode, then only a placeholder job_uid will be created.

    # TODO: Appropriately paramaterize the job json depending on user inputs
    and relevant file paths
    """
    if n_clicks:
        model_parameters, parameter_errors = extract_parameters_from_html(
            model_parameter_container
        )
        # Check if the model parameters are valid
        if parameter_errors:
            notification = generate_notification(
                "Model Parameters",
                "red",
                ANNOT_ICONS["parameters"],
                "Model parameters are not valid!",
            )
            return notification, no_update
        model_parameters["num_classes"] = len(all_annotations)
        model_parameters["network"] = model_name

        # Set io_parameters for inference, there will be no mask
        data_uri = tiled_datasets.get_data_uri_by_name(project_name)
        io_parameters = assemble_io_parameters_from_uris(data_uri, "")
        io_parameters["uid_retrieve"] = ""
        io_parameters["models_dir"] = RESULTS_DIR

        INFERENCE_PARAMS_EXAMPLE["params_list"][0]["params"][
            "io_parameters"
        ] = io_parameters
        INFERENCE_PARAMS_EXAMPLE["params_list"][0]["params"][
            "model_parameters"
        ] = model_parameters

        if MODE == "dev":
            job_uid = str(uuid.uuid4())
            job_message = f"Job has been succesfully submitted with uid: {job_uid}"
            notification_color = "indigo"
        else:
            if train_job_id is not None:
                job_name = get_flow_run_name(train_job_id)
                if job_name is not None:
                    children_flows = get_children_flow_run_ids(train_job_id)
                    # The first child flow is the training portion of the parent flow
                    # TODO: Maybe check number of children and type in the future
                    train_job_id = children_flows[0]

                    current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime(
                        "%Y/%m/%d %H:%M:%S"
                    )
                    flow_run_name = f"{job_name} {current_time}"

                    # Set the uid_retrieve of the inference job to the uid of the training job
                    INFERENCE_PARAMS_EXAMPLE["params_list"][0]["params"][
                        "io_parameters"
                    ]["uid_retrieve"] = train_job_id
                    INFERENCE_PARAMS_EXAMPLE["params_list"][0]["params"][
                        "io_parameters"
                    ]["job_name"] = flow_run_name
                    # TODO: Check if the architecture parameters are the same, as the one used in training
                    try:
                        # Schedule job
                        job_uid = schedule_prefect_flow(
                            FLOW_NAME,
                            parameters=INFERENCE_PARAMS_EXAMPLE,
                            flow_run_name=flow_run_name,
                            tags=PREFECT_TAGS + ["inference", project_name],
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
        data = get_flow_runs_by_name(tags=PREFECT_TAGS + ["train"])
    return data


@callback(
    Output("inference-job-selector", "data"),
    Output("inference-job-selector", "value"),
    Input("model-check", "n_intervals"),
    Input("train-job-selector", "value"),
    State("project-name-src", "value"),
)
def check_inference_job(n_intervals, train_job_id, project_name):
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
        return data, no_update
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
                    data = get_flow_runs_by_name(
                        flow_run_name=job_name,
                        tags=PREFECT_TAGS + ["inference", project_name],
                    )
                    selected_value = None if len(data) == 0 else no_update
                return data, selected_value
        return [], None


def populate_segmentation_results(
    job_id,
    project_name,
    job_type="training",
):
    """
    This function populates the segmentation results store based on the uids
    of the training job orinference job.
    """
    data_uri = tiled_datasets.get_data_uri_by_name(project_name)
    if job_id is not None:
        job_name = get_flow_run_name(job_id)
        if job_name is not None:
            children_flows = get_children_flow_run_ids(job_id)
            if job_type == "training":
                # Get second child to retrieve results
                job_id = children_flows[1]
            else:
                job_id = children_flows[0]
            expected_result_uri = f"{job_id}/seg_result"
            try:
                result_container = tiled_results.get_data_by_trimmed_uri(
                    expected_result_uri
                )
            except Exception:
                notification = generate_notification(
                    "Segmentation Results",
                    "red",
                    ANNOT_ICONS["results"],
                    f"Could not retrieve result from {job_type} job!",
                )
                return notification, None, children_flows[0]
            result_metadata = result_container.metadata
            if result_metadata["data_uri"] == data_uri:
                result_store = {
                    "seg_result_trimmed_uri": expected_result_uri,
                    "mask_idx": result_metadata["mask_idx"],
                    "data_uri": result_metadata["data_uri"],
                }
                notification = generate_notification(
                    "Segmentation Results",
                    "green",
                    ANNOT_ICONS["results"],
                    f"Retrieved result from {job_type} job!",
                )

                return notification, result_store, children_flows[0]
            else:
                return no_update, None, None
    return no_update, no_update, None


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Output("seg-results-train-store", "data"),
    Output("dvc-training-stats-link", "href"),
    Input("train-job-selector", "value"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def populate_segmentation_results_train(train_job_id, project_name):
    """
    This callback populates the segmentation results store based on the uids
    if the training job and the inference job.
    """
    notification, result_store, segment_job_id = populate_segmentation_results(
        train_job_id, project_name, "training"
    )
    if segment_job_id is not None:
        results_link = os.path.join(
            RESULTS_DIR, segment_job_id, "dvc_metrics/report.html"
        )
    else:
        results_link = no_update

    return notification, result_store, results_link


@callback(
    Output("notifications-container", "children", allow_duplicate=True),
    Output("seg-results-inference-store", "data"),
    Input("inference-job-selector", "value"),
    State("project-name-src", "value"),
    prevent_initial_call=True,
)
def populate_segmentation_results_inference(inference_job_id, project_name):
    """
    This callback populates the segmentation results store based on the uids
    if the training job and the inference job.
    """
    notification, result_store, _ = populate_segmentation_results(
        inference_job_id, project_name, "inference"
    )
    return (
        notification,
        result_store,
    )
