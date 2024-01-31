"""
   Copyright 2019-2022 Inmanta nv

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging
import os
from typing import Optional

import vymgmt
from pytest import fixture

LOGGER = logging.getLogger(__name__)


class VyosHelper:
    def __init__(self, router_ip: str) -> None:
        self.router_ip: str = router_ip
        self._console: Optional[vymgmt.Router] = None

    @property
    def console(self) -> vymgmt.Router:
        """Get a console connection to the router, details: https://vymgmt.readthedocs.io/en/latest/"""
        if self._console is None:
            self._console = vymgmt.Router(self.router_ip, "vyos", "vyos", 22)
            self._console.login()
        return self._console

    def close(self) -> None:
        if self._console is not None:
            self._console.logout()

    def clear(self) -> None:
        LOGGER.info("Cleaning Vyos Device")
        console = vymgmt.Router(self.router_ip, "vyos", "vyos", 22)
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
