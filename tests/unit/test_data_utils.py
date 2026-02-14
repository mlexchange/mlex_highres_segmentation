import importlib
import sys
from types import SimpleNamespace


class DummyMlflowAlgorithmClient:
    def __init__(self, *args, **kwargs):
        self.modelname_list = []

    def load_from_mlflow(self, algorithm_type="segmentation"):
        return None

    def __getitem__(self, key):
        raise KeyError(key)


class FakeContainer:
    def __init__(self, uri="tiled://root"):
        self.uri = uri
        self._children = {}
        self.metadata = None

    def keys(self):
        return self._children.keys()

    def create_container(self, key, metadata=None):
        container = FakeContainer(uri=f"{self.uri}/{key}")
        container.metadata = metadata
        self._children[key] = container
        return container

    def write_array(self, key, array):
        array_client = SimpleNamespace(uri=f"{self.uri}/{key}", array=array)
        self._children[key] = array_client
        return array_client

    def __getitem__(self, key):
        return self._children[key]


def test_save_annotations_data(mocker, monkeypatch):
    monkeypatch.setenv("DATA_TILED_URI", "http://example.com/api/v1/metadata/data")
    monkeypatch.setenv("MASK_TILED_URI", "http://example.com/api/v1/metadata/masks")
    monkeypatch.setenv("SEG_TILED_URI", "http://example.com/api/v1/metadata/seg")

    mocker.patch("tiled.client.from_uri", return_value={})
    mocker.patch(
        "mlex_utils.mlflow_utils.mlflow_algorithm_client.MlflowAlgorithmClient",
        DummyMlflowAlgorithmClient,
    )

    sys.modules.pop("utils.data_utils", None)
    data_utils = importlib.import_module("utils.data_utils")

    root_container = FakeContainer()
    mask_handler = data_utils.TiledMaskHandler.__new__(data_utils.TiledMaskHandler)
    mask_handler.mask_client = root_container

    mocker.patch.object(
        data_utils, "from_uri", return_value=SimpleNamespace(access_blob={})
    )
    mocker.patch.object(data_utils, "copy_tiled_access_info", return_value=None)
    mocker.patch.object(
        data_utils.tiled_datasets,
        "get_data_uri_by_trimmed_uri",
        return_value="http://example.com/data/project/sample",
    )
    mocker.patch.object(
        data_utils.tiled_datasets,
        "get_data_sequence_by_trimmed_uri",
        return_value=SimpleNamespace(access_blob={}),
    )

    all_annotations = [
        {
            "class_id": "class-1",
            "label": "Class 1",
            "color": "#ffffff",
            "annotations": {
                "0": [
                    {
                        "type": "rect",
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                    }
                ]
            },
        }
    ]

    uri, num_classes, message = mask_handler.save_annotations_data(
        global_store={"image_shapes": [(4, 4)]},
        all_annotations=all_annotations,
        trimmed_uri="project/sample",
    )

    assert uri is not None
    assert num_classes == 1
    assert message == "Annotations saved successfully."
    assert "project/sample" in uri

    user_container = root_container[data_utils.USER_NAME]
    project_container = user_container["project"]["sample"]
    assert len(list(project_container.keys())) == 1

    saved_hash = next(iter(project_container.keys()))
    saved_container = project_container[saved_hash]
    assert saved_container.metadata["project_name"] == "project/sample"
    assert "mask" in saved_container.keys()
