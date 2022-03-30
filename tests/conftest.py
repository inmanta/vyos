import os

import vymgmt
from pytest import fixture


@fixture
def vy_host():
    return os.environ["VY_TEST_HOST"]


@fixture
def console(vy_host):
    vyos = vymgmt.Router(vy_host, "vyos", "vyos", 22)
    vyos.login()
    yield vyos
    vyos.logout()


@fixture
def clear(vy_host):
    console = vymgmt.Router(vy_host, "vyos", "vyos", 22)
    console.login()
    out = console.run_op_mode_command(
        "sudo rm /opt/vyatta/etc/config/ipsec.d/rsa-keys/localhost.key /config/ipsec.d/rsa-keys/localhost.key"
    )
    console.configure()
    console.run_conf_mode_command("load /config/clear.config")
    out = console.run_conf_mode_command("commit")
    console.exit(force=True)
    console.logout()
    assert "Traceback" not in out


@fixture
def vyos_device(clear, vy_host):
    """
    New, cleaner name for clear fixture, intended to replace clear
    """
    return vy_host
