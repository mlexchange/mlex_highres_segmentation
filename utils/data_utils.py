import json
import os
import uuid

import httpx
import numpy as np
import requests
from dotenv import load_dotenv
from tiled.client import from_uri
from tiled.client.array import ArrayClient
from tiled.client.container import Container

from utils.annotations import Annotations


def DEV_download_google_sample_data():
    """
    Download sample project images to data/ folder, this only happens once,
    after that the download is skipped if the data exists.
    """

    def download_file(url, destination):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    sample_data_links = {
        "check_handedness": [
            "https://drive.google.com/u/0/uc?id=1l42VFZcmVOITL3-eqCKVX_u3PDc7Vkw7&export=download",
            "https://drive.google.com/u/0/uc?id=1Glio8R-ur65iESK8cvjg7uUHXWnY1odx&export=download",
        ],
        "clay_testZMQ": [
            "https://drive.google.com/uc?export=download&id=1GCkK65bBAU79M6grHDKeTUJaeHl-bNgT",  # slice 200
            "https://drive.google.com/uc?export=download&id=1Jp1TEdl2tkerqIaDIR4CCL1tKDM3Tc5G",  # slice 201
        ],
        "seg-clay_testZMQ": [
            "https://drive.google.com/uc?export=download&id=15MwMHHLR6jWSE8uV2iS3AqkDQWnP-R3d",  # slice 200
            "https://drive.google.com/uc?export=download&id=1XyIzbKXBud8kmUrSxPnFFmTfUMfI9wQo",  # slice 201        ],
        ],
    }
    base_directory = "data"

    print("Downloading sample data...")
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    for project, urls in sample_data_links.items():
        project_directory = os.path.join(base_directory, project)
        if not os.path.exists(project_directory):
            os.makedirs(project_directory)

        for i, url in enumerate(urls):
            destination = os.path.join(project_directory, f"{i}.tiff")

            if os.path.exists(destination):
                print(f"File {destination} already exists. Skipping download.")
                continue

            download_file(url, destination)
            print(f"Downloaded {destination}")

    print("All files downloaded successfully.")


def DEV_load_exported_json_data(file_path, USER_NAME, PROJECT_NAME):
    """
    This function is used to load the exported json, which was saved in a local file.
    User name is used to filter the data by user.
    Project name is used to filter the data by project.
    It is sorted by timestamp with the latest timestamp first.

    TODO: this function will be replaced with a database query in the future.
    """
    DATA_JSON = []

    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                json_data = json.loads(line)
                json_data["data"] = json.loads(json_data["data"])
                DATA_JSON.append(json_data)

    data = [
        data
        for data in DATA_JSON
        if data["user"] == USER_NAME and data["source"] == PROJECT_NAME
    ]
    if data:
        data = sorted(data, key=lambda x: x["time"], reverse=True)

    return data


def DEV_filter_json_data_by_timestamp(data, timestamp):
    return [data for data in data if data["time"] == timestamp]


load_dotenv()

TILED_URI = os.getenv("TILED_URI")
TILED_API_KEY = os.getenv("TILED_API_KEY")
LOCAL_MODE = os.getenv("TILED_DEPLOYMENT_LOC")
USER_NAME = os.getenv("USER_NAME", "user1")

if os.getenv("TILED_DEPLOYMENT_LOC", "") == "Local":
    print("To run a Tiled server locally run the bash script `./tiled_serve_dir.sh`.")
    print("This requires to additionally install the server components of Tiled with:")
    print('`pip install "tiled[server]"`')
    DEV_download_google_sample_data()
    client = from_uri("http://localhost:8000")
    data = client
else:
    client = from_uri(TILED_URI, api_key=TILED_API_KEY, timeout=httpx.Timeout(30.0))
    data = client["reconstruction"]


def get_data_project_names():
    """
    Get available project names from the main Tiled container,
    filtered by types that can be processed (Container and ArrayClient)
    """
    if LOCAL_MODE == "Local":
        project_names = [
            project
            for project in list(data)
            if isinstance(data[project], (Container, ArrayClient))
        ]
        return project_names
    else:
        # TODO: remove hard-coded names when caching is implemented
        return [
            "rec20191210_111800_lobster-claw_acid_vs_not_2_bin2",
            "rec20190524_085542_clay_testZMQ_8bit",
            "rec20221222_085501_looking_from_above_spiralUP_CounterClockwise_endPointAtDoor",
            "seg-rec20190524_085542_clay_testZMQ_8bit",
            "RECON_20180227_110041_bamboo_wet_bent_cropped",
        ]


def get_data_sequence_by_name(project_name):
    """
    Data sequences may be given directly inside the main client container,
    but can also be additionally encapsulated in a folder.
    """
    project_client = data[project_name]
    # If the project directly points to an array
    if isinstance(project_client, ArrayClient):
        return project_client
    # If project_name points to a container
    elif isinstance(project_client, Container):
        # Enter the container and return first element
        if len(list(project_client)) == 1:
            sequence_client = project_client.values()[0]
            if isinstance(sequence_client, ArrayClient):
                return sequence_client
    return None


def get_data_shape_by_name(project_name):
    """
    Retrieve shape of the data
    """
    project_container = get_data_sequence_by_name(project_name)
    if project_container:
        return project_container.shape
    return None


def get_annotated_segmented_results(json_file_path="exported_annotation_data.json"):
    annotated_slices = []
    with open(json_file_path, "r") as f:
        for line in f:
            if line.strip():
                json_data = json.loads(line)
                json_data["data"] = json.loads(json_data["data"])
                annotated_slices = list(json_data["data"][0]["annotations"].keys())
    return annotated_slices


def save_annotations_data(global_store, all_annotations, project_name):
    """
    Transforms annotations data to a pixelated mask and outputs to the Tiled server
    """
    annotations = Annotations(all_annotations, global_store)
    # TODO: Check sparse status
    annotations.create_annotation_mask(sparse=False)

    # Get metadata and annotation data
    metadata = annotations.get_annotations()
    mask = annotations.get_annotation_mask()

    # Get raw images associated with each annotated slice
    img_idx = list(metadata.keys())
    metadata["indices"] = img_idx
    try:
        mask = np.stack(mask)
    except ValueError:
        return "No annotations to process."

    "Store the mask in the Tiled server under mlex_store/username/project_name/uid/mask"
    container_keys = ["mlex_store", USER_NAME, project_name, str(uuid.uuid4())]
    last_container = client
    for key in container_keys:
        if key not in last_container.keys():
            last_container = last_container.create_container(key=key)
        else:
            last_container = last_container[key]
    mask = last_container.write_array(key="mask", array=mask, metadata=metadata)
    # print("Created a mask array with the following uri: ", mask.uri)
    return mask.uri
