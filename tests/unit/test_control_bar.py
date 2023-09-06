from callbacks.control_bar import reset_filters
import pytest
import numpy as np


class TiledDataMock:
    def __init__(self):
        self["sample_project"] = np.zeros(500, 500, 500)


@pytest.fixture
def nclicks():
    return True


def test_reset_filters(nclicks, mocker):
    mocker.patch("utils.data_utils.client", new=TiledDataMock())
    assert reset_filters(nclicks) == 100
