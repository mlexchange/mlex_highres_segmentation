from callbacks.control_bar import reset_filters
import pytest


@pytest.fixture
def nclicks():
    return True


def test_reset_filters(nclicks):
    default_brightness, default_contrast = reset_filters(nclicks)
    assert default_brightness == 100
    assert default_contrast == 100
