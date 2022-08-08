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


def test_interface_in_bridge(project, vyos):
    project.compile(
        f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vyos.router_ip}")

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        bridge_group=br0,
    )

    br0 = vyos::Bridge(
        host=r1,
        name="br0",
    )
    """,
    )

    eth1 = project.get_resource("vyos::Config", node="interfaces ethernet eth1")
    br0 = project.get_resource("vyos::Config", node="interfaces bridge br0")

    assert eth1.id in br0.requires

    project.deploy_resource("vyos::Config", node="interfaces ethernet eth1")

    compare = project.dryrun_resource("vyos::Config", node="interfaces bridge br0")
    assert compare

    project.deploy_resource("vyos::Config", node="interfaces bridge br0")

    compare = project.dryrun_resource("vyos::Config", node="interfaces bridge br0")
    assert not compare
