from pytest import fixture
import os

@fixture
def vy_host():
    return os.environ["VY_TEST_HOST"]
