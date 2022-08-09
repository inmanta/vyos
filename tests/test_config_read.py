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
import random
import string

import inmanta.agent.handler


def test_basics(project, vyos):

    hostname = "".join(random.choice(string.ascii_letters) for x in range(10))

    project.compile(
        f"""
import vyos

r1 = vyos::Host(
    name="{hostname}",
    user="vyos",
    password="vyos",
    ip="{vyos.router_ip}"
    )

vyos::Hostname(host=r1, name=r1.name)
"""
    )

    resource = project.get_resource("vyos::Config")
    handler = project.get_handler(resource, False)

    ctx = inmanta.agent.handler.HandlerContext(resource)

    vyos = handler.get_connection(ctx, resource.id.version, resource)

    rawcfg = handler.get_config_dict(ctx, resource, vyos)

    assert "system" in rawcfg

    compare = project.dryrun_resource("vyos::Config")
    assert "system host-name" in compare
