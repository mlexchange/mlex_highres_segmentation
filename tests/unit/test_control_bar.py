from callbacks.control_bar import reset_filters
import pytest
import numpy as np

class TiledDataMock:
    def __init__(self):
        self["sample_project"] = np.zeros(500, 500, 500)




@pytest.fixture
def nclicks():
    return True


def test_reset_filters(nclicks):
    mocker.patch("constants.DATA", new=TiledDataMock())
    default_brightness, default_contrast = reset_filters(nclicks)
    assert default_brightness == 100
    assert default_contrast == 100
