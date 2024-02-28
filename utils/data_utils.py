import json
import os

import httpx
import numpy as np
from dotenv import load_dotenv
from tiled.client import from_uri
from tiled.client.array import ArrayClient
from tiled.client.container import Container

from utils.annotations import Annotations

load_dotenv()

DATA_TILED_URI = os.getenv("DATA_TILED_URI")
DATA_TILED_API_KEY = os.getenv("DATA_TILED_API_KEY")


class TiledDataLoader:
    def __init__(
        self, data_tiled_uri=DATA_TILED_URI, data_tiled_api_key=DATA_TILED_API_KEY
    ):
        self.data_tiled_uri = data_tiled_uri
        self.data_tiled_api_key = data_tiled_api_key
        self.data_client = from_uri(
            self.data_tiled_uri,
            api_key=self.data_tiled_api_key,
            timeout=httpx.Timeout(30.0),
        )

    def refresh_data_client(self):
        self.data_client = from_uri(
            self.data_tiled_uri,
            api_key=self.data_tiled_api_key,
            timeout=httpx.Timeout(30.0),
        )

    def get_data_project_names(self):
        """
        Get available project names from the main Tiled container,
        filtered by types that can be processed (Container and ArrayClient)
        """
        project_names = [
            project
            for project in list(self.data_client)
            if isinstance(self.data_client[project], (Container, ArrayClient))
        ]
        return project_names

    def get_data_sequence_by_name(self, project_name):
        """
        Data sequences may be given directly inside the main client container,
        but can also be additionally encapsulated in a folder, multiple container or in a .nxs file.
        We make use of specs to figure out the path to the 3d data.
        """
        project_client = self.data_client[project_name]
        # If the project directly points to an array, directly return it
        if isinstance(project_client, ArrayClient):
            return project_client
        # If project_name points to a container
        elif isinstance(project_client, Container):
            # Check if the specs give us information about which sub-container to access
            specs = project_client.specs
            if any(spec.name == "NXtomoproc" for spec in specs):
                # Example for how to access data if the project container corresponds to a
                # nexus-file following the NXtomoproc definition
                # TODO: This assumes that a validator has checked the file on ingestion
                # Otherwise we should first test if the path holds data
                return project_client["entry/data/data"]
            # Enter the container and return first element
            # if it represents an array
            if len(list(project_client)) == 1:
                sequence_client = project_client.values()[0]
                if isinstance(sequence_client, ArrayClient):
                    return sequence_client
        return None

    def get_data_shape_by_name(self, project_name):
        """
        Retrieve shape of the data
        """
        project_container = self.get_data_sequence_by_name(project_name)
        if project_container:
            return project_container.shape
        return None

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

    def save_annotations_data(self, global_store, all_annotations, project_name):
        """
        Transforms annotations data to a pixelated mask and outputs to
        the Tiled server

        # TODO: Save data to Tiled server after transformation
        """
        annotations = Annotations(all_annotations, global_store)
        annotations.create_annotation_mask(sparse=True)  # TODO: Check sparse status

        # Get metadata and annotation data
        metadata = annotations.get_annotations()
        mask = annotations.get_annotation_mask()

        # Get raw images associated with each annotated slice
        img_idx = list(metadata.keys())
        img = self.data[project_name]
        raw = []
        for idx in img_idx:
            ar = img[int(idx)]
            raw.append(ar)
        try:
            raw = np.stack(raw)
            mask = np.stack(mask)
        except ValueError:
            return "No annotations to process."

        return


tiled_dataset = TiledDataLoader()
