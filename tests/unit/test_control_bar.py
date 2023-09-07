import pytest
import numpy as np


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
    from callbacks.control_bar import reset_filters
    assert reset_filters(nclicks) == 100
