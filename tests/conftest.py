from pytest import fixture
import os
import vymgmt

@fixture
def vy_host():
    return os.environ["VY_TEST_HOST"]


@fixture
def console(vy_host):
    vyos = vymgmt.Router(vy_host, "vyos", "vyos", 22)
    vyos.login()
    yield vyos
    vyos.logout()