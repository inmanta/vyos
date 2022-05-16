import os
from typing import Optional

import vymgmt
from pytest import fixture


class VyosHelper:
    def __init__(self, router_ip: str) -> None:
        self.router_ip: str = router_ip
        self.console: Optional[vymgmt.Router] = None

    @property
    def console(self) -> vymgmt.Router:
        """Get a console connection to the router, details: https://vymgmt.readthedocs.io/en/latest/"""
        if self.console is None:
            self.console = vymgmt.Router(vy_host, "vyos", "vyos", 22)
            self.console.login()
        return self.console

    def close(self) -> None:
        if self.console is not None:
            self.console.logout()

    def clear(self) -> None:
        console = vymgmt.Router(vy_host, "vyos", "vyos", 22)
        console.login()
        out = console.run_op_mode_command(
            "sudo rm /opt/vyatta/etc/config/ipsec.d/rsa-keys/localhost.key /config/ipsec.d/rsa-keys/localhost.key"
        )
        console.configure()
        console.run_conf_mode_command("load /config/clear.config")
        console.run_conf_mode_command("commit")
        console.exit(force=True)
        console.logout()
        assert "Traceback" not in out


@fixture
def vyos(vy_host) -> VyosHelper:
    helper = VyosHelper(vy_host)
    helper.clear()
    yield helper
    helper.close()


@fixture
def vy_host():
    return os.environ["VY_TEST_HOST"]


@fixture
def console(vyos):
    return vyos.console


@fixture
def clear(vyos):
    # Functionality subsumed by vyos
    pass


@fixture
def vyos_device(vyos, vy_host):
    """
    New, cleaner name for clear fixture, intended to replace clear
    """
    return vy_host
