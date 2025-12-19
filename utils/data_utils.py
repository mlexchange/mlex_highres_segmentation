import json
import os
import traceback
from urllib.parse import urlparse, urlunparse

import httpx
import numpy as np
from dotenv import load_dotenv
from mlex_utils.mlflow_utils.mlflow_algorithm_client import MlflowAlgorithmClient
from tiled.client import from_uri
from tiled.client.array import ArrayClient
from tiled.client.container import Container

from utils.annotations import Annotations

load_dotenv()

DATA_TILED_URI = os.getenv("DATA_TILED_URI")
DATA_TILED_API_KEY = os.getenv("DATA_TILED_API_KEY")
MASK_TILED_URI = os.getenv("MASK_TILED_URI")
MASK_TILED_API_KEY = os.getenv("MASK_TILED_API_KEY")
SEG_TILED_URI = os.getenv("SEG_TILED_URI")
SEG_TILED_API_KEY = os.getenv("SEG_TILED_API_KEY")
USER_NAME = os.getenv("USER_NAME", "user1")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_TRACKING_USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME", "")
MLFLOW_TRACKING_PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD", "")


def _create_or_return_containers(client, container_names):
    """
    Iterates through a list of container names and creates them if they do not exist.
    For example, if the container_names are ["results", "segmentation"], it will return the Tiled client for
    client["results"]["segmentation"], having created any containers that were missing.
    """
    for container_name in container_names:
        if container_name not in client.keys():
            client = client.create_container(key=container_name)
        else:
            client[container_name]
    return client


def _split_base_uri_containers(uri):
    """
    Splits the base uri from the containers and returns both base uri and a container list.
    This assumes that the given uri contains an api version string, metadata and container names
    # separated by slashes, e.g. api/v1/metadata/masks/special_container
    """
    parsed_url = urlparse(uri)
    path = parsed_url.path
    # Path is either empty or contains a leading slash only
    if len(path) < 2:
        return uri, []

    # Check if the path contain an api string that could be followed by containers
    if "/api" not in path:
        return uri, []

    # TODO: Allow more flexible splitting of the path, using other api endpoints
    path_pieces = path.split("/metadata", 1)
    base_uri = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            path_pieces[0],
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
    container_names = (
        path_pieces[1].strip("/").split("/") if len(path_pieces) > 1 else []
    )
    return base_uri, container_names


class TiledDataLoader:
    def __init__(
        self,
        data_tiled_uri=DATA_TILED_URI,
        data_tiled_api_key=DATA_TILED_API_KEY,
    ):
        """
        Initialize a Tiled data loader with the given uri and api key.
        """
        self.data_tiled_uri = data_tiled_uri
        self.data_tiled_api_key = data_tiled_api_key
        self.refresh_data_client()

    def refresh_data_client(self):
        try:
            self.data_client = from_uri(
                self.data_tiled_uri,
                api_key=self.data_tiled_api_key,
                timeout=httpx.Timeout(30.0),
            )
        except Exception as e:
            print(f"Error connecting to Tiled: {e}")
            traceback.print_exc()
            self.data_client = None

    def check_dataloader_ready(self, base_uri_only=False):
        """
        Check if the data client is available and ready to be used.
        If base_only is True, only check the base uri.
        """
        if self.data_client is None:
            if base_uri_only:
                base_uri, _ = _split_base_uri_containers(self.data_tiled_uri)
                try:
                    from_uri(
                        base_uri,
                        api_key=self.data_tiled_api_key,
                        timeout=httpx.Timeout(30.0),
                    )
                    return True
                except Exception as e:
                    print(f"Error connecting to Tiled: {e}")
                    return False
            else:
                # Try refreshing once
                self.refresh_data_client()
                return False if self.data_client is None else True
        return True

    def get_base_uri_initial_path(self):
        """
        Get the base uri of the Tiled server,
        without any container names and the path to the root container
        """
        base_uri, root_path = _split_base_uri_containers(self.data_tiled_uri)
        root_path = "/".join(root_path)
        return base_uri, root_path

    def get_data_project_names(self):
        """
        Get available project names from the main Tiled container,
        filtered by types that can be processed (Container and ArrayClient)
        """
        if self.data_client is None:
            return []
        project_names = [
            project
            for project in list(self.data_client)
            if isinstance(self.data_client[project], (Container, ArrayClient))
        ]
        return project_names

    def get_data_sequence_by_trimmed_uri(self, trimmed_uri):
        """
        Data sequences may be given directly inside the main client container,
        but can also be additionally encapsulated in a folder, multiple container or in a .nxs file.
        We make use of specs to figure out the path to the 3d data.
        """
        if self.data_client is None or trimmed_uri is None:
            return None
        sequence_client = self.data_client[trimmed_uri]
        # If the project directly points to an array, directly return it
        if isinstance(sequence_client, ArrayClient):
            return sequence_client
        # If sequence_client points to a container
        elif isinstance(sequence_client, Container):
            # Check if the specs give us information about which sub-container to access
            specs = sequence_client.specs
            # TODO: Read yaml file with spec to path mapping
            if any(spec.name == "NXtomoproc" for spec in specs):
                # Example for how to access data if the project container corresponds to a
                # nexus-file following the NXtomoproc definition
                # TODO: This assumes that a validator has checked the file on ingestion
                # Otherwise we should first test if the path holds data
                return sequence_client["entry/data/data"]
            # Enter the container and return first element
            # if it represents an array
            if len(list(sequence_client)) == 1:
                sequence_client = sequence_client.values()[0]
                if isinstance(sequence_client, ArrayClient):
                    return sequence_client
        return None

    def get_data_shape_by_trimmed_uri(self, trimmed_uri):
        """
        Retrieve shape of the data
        """
        sequence_client = self.get_data_sequence_by_trimmed_uri(trimmed_uri)
        if sequence_client:
            return sequence_client.shape
        return None

    def get_data_uri_by_trimmed_uri(self, trimmed_uri):
        """
        Retrieve full uri of the data from the trimmed uri
        """
        sequence_client = self.get_data_sequence_by_trimmed_uri(trimmed_uri)
        if sequence_client:
            return sequence_client.uri
        return None

    def get_data_slice_by_trimmed_uri(self, trimmed_uri, slice=None):
        """
        Retrieve data by a trimmed uri (not containing the base uri) and slice id
        """
        if slice is None:
            return self.data_client[trimmed_uri]
        else:
            return self.data_client[trimmed_uri][slice]


tiled_datasets = TiledDataLoader(
    data_tiled_uri=DATA_TILED_URI, data_tiled_api_key=DATA_TILED_API_KEY
)


class TiledMaskHandler:
    """
    This class is used to handle the masks that are generated from the annotations.
    """

    def __init__(
        self,
        mask_tiled_uri=MASK_TILED_URI,
        mask_tiled_api_key=MASK_TILED_API_KEY,
    ):
        self.mask_tiled_uri = mask_tiled_uri
        self.mask_tiled_api_key = mask_tiled_api_key

        self.refresh_mask_handler()

    def refresh_mask_handler(self):
        base_uri, container_names = _split_base_uri_containers(self.mask_tiled_uri)
        try:
            base_client = from_uri(
                base_uri,
                api_key=self.mask_tiled_api_key,
                timeout=httpx.Timeout(30.0),
            )
            self.mask_client = _create_or_return_containers(
                base_client, container_names
            )
        except Exception as e:
            print(f"Error connecting to Tiled: {e}")
            traceback.print_exc()
            self.mask_client = None

    def check_mask_handler_ready(self):
        if self.mask_client is None:
            # Try refreshing once
            self.refresh_mask_handler()
            return False if self.mask_client is None else True
        return True

    @staticmethod
    def get_annotated_segmented_results(json_file_path="exported_annotation_data.json"):
        annotated_slices = []
        with open(json_file_path, "r") as f:
            for line in f:
                if line.strip():
                    json_data = json.loads(line)
                    json_data["data"] = json.loads(json_data["data"])
                    annotated_slices = list(json_data["data"][0]["annotations"].keys())
        return annotated_slices

    @staticmethod
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

    @staticmethod
    def DEV_filter_json_data_by_timestamp(data, timestamp):
        return [data for data in data if data["time"] == timestamp]

    def save_annotations_data(self, global_store, all_annotations, trimmed_uri):
        """
        Transforms annotations data to a pixelated mask and outputs to the Tiled server
        """
        if "image_shapes" in global_store:
            image_shape = global_store["image_shapes"][0]
        else:
            data_shape = (
                tiled_datasets.get_data_shape_by_trimmed_uri(trimmed_uri)
                if trimmed_uri
                else None
            )
            if data_shape is None:
                return None, None, "Image shape could not be determined."
            image_shape = (data_shape[1], data_shape[2])

        # ===== ADD THIS BLOCK - Filter out SAM3 polygons =====
        filtered_annotations = []
        for annotation_class in all_annotations:
            filtered_class = annotation_class.copy()
            filtered_class["annotations"] = {}

            for slice_idx, slice_annotations in annotation_class["annotations"].items():
                manual_only = [
                    s for s in slice_annotations if s.get("source") != "sam3"
                ]
                if manual_only:
                    filtered_class["annotations"][slice_idx] = manual_only

            filtered_annotations.append(filtered_class)

        annotations = Annotations(filtered_annotations, image_shape)
        # ===== END OF ADDED BLOCK =====
        # TODO: Check sparse status, it may be worthwhile to store the mask as a sparse array
        # if our machine learning models can handle sparse arrays
        annotations.create_annotation_mask(sparse=False)

        # Get metadata and annotation data
        annnotations_per_slice = annotations.get_annotations()
        annotation_classes = annotations.get_annotation_classes()
        annotations_hash = annotations.get_annotations_hash()

        metadata = {
            "project_name": trimmed_uri,
            "data_uri": tiled_datasets.get_data_uri_by_trimmed_uri(trimmed_uri),
            "image_shape": image_shape,
            "mask_idx": [int(key) for key in annnotations_per_slice.keys()],
            "classes": annotation_classes,
            "annotations": annnotations_per_slice,
            "unlabeled_class_id": -1,
        }

        mask = annotations.get_annotation_mask()

        try:
            mask = np.stack(mask)
        except ValueError:
            return None, None, "No annotations to process."

        # Store the mask in the Tiled server under /username/<trimmed_uri>/uuid/mask"
        # This replicates the structure of the data uri under the user name
        container_keys = [USER_NAME] + trimmed_uri.strip("/").split("/")
        last_container = self.mask_client
        for key in container_keys:
            if key not in last_container.keys():
                last_container = last_container.create_container(key=key)
            else:
                last_container = last_container[key]

        # Add json metadata to a container with the md5 hash as key
        # if a mask with that hash does not already exist
        if annotations_hash not in last_container.keys():
            last_container = last_container.create_container(
                key=annotations_hash, metadata=metadata
            )
            mask = last_container.write_array(key="mask", array=mask)
        else:
            last_container = last_container[annotations_hash]
        return (
            last_container.uri,
            len(annotation_classes),
            "Annotations saved successfully.",
        )

    # ===== ADD THIS NEW METHOD HERE =====
    def save_sam3_masks_data(self, global_store, all_annotations, trimmed_uri):
        """
        Save SAM3-refined masks to Tiled by reading current SAM3 annotations from annotation-class-store.
        Ignores the sam3_masks parameter and always uses current polygons.
        """
        if "image_shapes" in global_store:
            image_shape = global_store["image_shapes"][0]
        else:
            data_shape = (
                tiled_datasets.get_data_shape_by_trimmed_uri(trimmed_uri)
                if trimmed_uri
                else None
            )
            if data_shape is None:
                return None, None, "Image shape could not be determined."
            image_shape = (data_shape[1], data_shape[2])

        # Filter to keep ONLY SAM3 annotations (source="sam3")
        filtered_annotations = []
        for annotation_class in all_annotations:
            filtered_class = annotation_class.copy()
            filtered_class["annotations"] = {}

            for slice_idx, slice_annotations in annotation_class["annotations"].items():
                sam3_only = [
                    s for s in slice_annotations if s.get("source") == "sam3"
                ]
                if sam3_only:
                    filtered_class["annotations"][slice_idx] = sam3_only

            filtered_annotations.append(filtered_class)

        annotations = Annotations(filtered_annotations, image_shape)
        annotations.create_annotation_mask(sparse=False)

        annotations_per_slice = annotations.get_annotations()
        annotation_classes = annotations.get_annotation_classes()
        annotations_hash = annotations.get_annotations_hash()

        metadata = {
            "project_name": trimmed_uri,
            "data_uri": tiled_datasets.get_data_uri_by_trimmed_uri(trimmed_uri),
            "image_shape": image_shape,
            "mask_idx": [int(key) for key in annotations_per_slice.keys()],
            "classes": annotation_classes,
            "annotations": annotations_per_slice,
            "unlabeled_class_id": -1,
            "mask_source": "sam3",
        }

        mask = annotations.get_annotation_mask()

        try:
            mask = np.stack(mask)
        except ValueError:
            return None, None, "No SAM3 annotations to process."

        container_keys = [USER_NAME] + trimmed_uri.strip("/").split("/")
        last_container = self.mask_client
        for key in container_keys:
            if key not in last_container.keys():
                last_container = last_container.create_container(key=key)
            else:
                last_container = last_container[key]

        if annotations_hash not in last_container.keys():
            last_container = last_container.create_container(
                key=annotations_hash, metadata=metadata
            )
            mask = last_container.write_array(key="mask", array=mask)
        else:
            last_container = last_container[annotations_hash]
        
        return (
            last_container.uri,
            len(annotation_classes),
            "SAM3 masks saved successfully.",
        )



tiled_masks = TiledMaskHandler(
    mask_tiled_uri=MASK_TILED_URI,
    mask_tiled_api_key=MASK_TILED_API_KEY,
)

tiled_results = TiledDataLoader(
    data_tiled_uri=SEG_TILED_URI,
    data_tiled_api_key=SEG_TILED_API_KEY,
)


class Models:
    """
    This class loads algorithm definitions from MLflow instead of a local JSON file.
    """

    def __init__(self):
        # Initialize MLflow client
        self.mlflow_client = MlflowAlgorithmClient(
            MLFLOW_TRACKING_URI,
            MLFLOW_TRACKING_USERNAME,
            MLFLOW_TRACKING_PASSWORD,
        )

        # Load algorithms from MLflow filtered by type="segmentation"
        self.mlflow_client.load_from_mlflow(algorithm_type="segmentation")

        # Get list of model names
        self.modelname_list = self.mlflow_client.modelname_list

    def __getitem__(self, key):
        """Get model by name from MLflow"""
        try:
            return self.mlflow_client[key]
        except KeyError:
            raise KeyError(f"A model with name {key} does not exist.")


models = Models()


def extract_parameters_from_html(model_parameters_html):
    """
    Extracts parameters from the children component of a ParameterItems component,
    if there are any errors in the input, it will return an error status
    """
    errors = False
    input_params = {}
    for param in model_parameters_html["props"]["children"]:
        # param["props"]["children"][0] is the label
        # param["props"]["children"][1] is the input
        parameter_container = param["props"]["children"][1]
        # The actual parameter item is the first and only child of the parameter container
        parameter_item = parameter_container["props"]["children"]["props"]
        key = parameter_item["id"]["param_key"]
        if "value" in parameter_item:
            value = parameter_item["value"]
        elif "checked" in parameter_item:
            value = parameter_item["checked"]
        if "error" in parameter_item:
            if parameter_item["error"] is not False:
                errors = True
        input_params[key] = value
    return input_params, errors


def assemble_io_parameters_from_uris(data_uri, mask_uri):
    """
    Assembles input and output Tiled information for the model
    """
    io_parameters = {
        "data_tiled_uri": data_uri,
        "mask_tiled_uri": mask_uri,
        "seg_tiled_uri": SEG_TILED_URI,
    }
    return io_parameters
