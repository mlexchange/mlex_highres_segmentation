import sys

import numpy as np
import pytest


class DummyMlflowAlgorithmClient:
    def __init__(self, *args, **kwargs):
        self.modelname_list = []

    def load_from_mlflow(self, algorithm_type="segmentation"):
        return None

    def __getitem__(self, key):
        raise KeyError(key)


@pytest.fixture
def tiled_data_mock():
    return {"sample_project": np.zeros((500, 500, 500)), "reconstruction": 0}


@pytest.fixture
def nclicks():
    return True


def test_reset_filters(mocker, nclicks, tiled_data_mock):
    mocker.patch(
        "tiled.client.from_uri",
        return_value=tiled_data_mock,
    )
    mocker.patch(
        "mlex_utils.mlflow_utils.mlflow_algorithm_client.MlflowAlgorithmClient",
        DummyMlflowAlgorithmClient,
    )
    sys.modules.pop("callbacks.control_bar", None)
    sys.modules.pop("utils.data_utils", None)
    from callbacks.control_bar import reset_filters

    assert reset_filters(nclicks) == 100
