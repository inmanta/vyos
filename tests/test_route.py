from typing import Iterable, Optional

import pytest


def convert_bool(val):
    return "true" if val else "false"


def test_static_route(project, vy_host, clear):
    def make_config(purge=False):
        project.compile(
            f"""
    import vyos
    import vyos::vpn

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    vyos::StaticRoute(
        host=r1,
        next_hop = "10.100.100.1",
        destination= "10.100.100.1/32",
        purged={convert_bool(purge)}
    )
        """
        )

    make_config()

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0

    make_config(purge=True)

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0


@pytest.mark.parametrize(
    "source_is_set,dest_is_set,protocol_is_set,description_is_set",
    [
        (False, False, False, False),
        (True, False, False, False),
        (True, True, False, False),
        (True, True, True, False),
        (True, True, True, True),
    ],
)
def test_policy_route(
    project,
    vy_host,
    clear,
    source_is_set: bool,
    dest_is_set: bool,
    protocol_is_set: bool,
    description_is_set: bool,
) -> None:
    def unlines_optional(lines: Iterable[Optional[str]]) -> str:
        return "\n".join(line for line in lines if line is not None)

    def make_config(purge=False):
        project.compile(
            f"""
    import vyos

    r1 = vyos::Host(
        name = "lab1",
        user = "vyos",
        password = "vyos",
        ip = "{vy_host}",
    )

    vyos::PolicyRoute(
        host = r1,
        name = "T2",
        rule = 1,
        table = 2,
        %s
        purged = {convert_bool(purge)}
    )
            """
            % ",".join(
                line
                for line in [
                    "source_address = '192.168.100.104/29'" if source_is_set else None,
                    "destination_address = '192.168.2.2/29'" if dest_is_set else None,
                    "protocol = 'tcp'" if protocol_is_set else None,
                    "description = 'my description'" if description_is_set else None,
                    # make sure trailing comma is added when at least one line present
                    "",
                ]
                if line is not None
            ),
        )

    make_config()

    assert project.get_resource("vyos::Config").config.strip() == "\n".join(
        f"policy route T2 rule 1 {line}"
        for line in [
            "set table '2'",
            "source address '192.168.100.104/29'" if source_is_set else None,
            "destination address '192.168.2.2/29'" if dest_is_set else None,
            "protocol 'tcp'" if protocol_is_set else None,
            "description 'my description'" if description_is_set else None,
        ]
        if line is not None
    )

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    print(compare)
    assert len(compare) == 0

    make_config(purge=True)

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0
