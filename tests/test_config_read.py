import random
import string

import inmanta.agent.handler


def test_basics(project, clear, vy_host):

    hostname = "".join(random.choice(string.ascii_letters) for x in range(10))

    project.compile(
        f"""
import vyos

r1 = vyos::Host(
    name="{hostname}",
    user="vyos",
    password="vyos",
    ip="{vy_host}"
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
