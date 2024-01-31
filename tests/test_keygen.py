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

from inmanta.agent import handler


def convert_bool(val):
    return "true" if val else "false"


def test_keygen(project, vyos):
    def make_config(purge=False):
        project.compile(
            f"""
    import vyos
    import vyos::vpn

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vyos.router_ip}")

    vyos::vpn::KeyGen(host=r1)
        """
        )

    make_config()

    compare = project.dryrun_resource("vyos::vpn::KeyGen")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::vpn::KeyGen")

    compare = project.dryrun_resource("vyos::vpn::KeyGen")
    assert len(compare) == 0

    resource = project.get_resource("vyos::vpn::KeyGen")
    myhandler = project.get_handler(resource, False)
    ctx = handler.HandlerContext(resource)
    facts = myhandler.facts(ctx, resource)
    assert "key" in facts
    assert len(facts["key"]) > 5
