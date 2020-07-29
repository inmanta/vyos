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
    "source_a_is_set,dest_a_is_set,source_p_is_set,dest_p_is_set,protocol_is_set,description_is_set",
    [
        (False, False, False, False, False, False),
        (True, False, False, False, False, False),
        (False, True, False, False, False, False),
        (False, False, True, False, True, False),
        (False, False, False, True, True, False),
        (False, False, False, False, True, False),
        (False, False, False, False, False, True),
        (True, True, True, True, True, True),
    ],
)
def test_policy_route(
    project,
    vy_host,
    clear,
    source_a_is_set: bool,
    dest_a_is_set: bool,
    source_p_is_set: bool,
    dest_p_is_set: bool,
    protocol_is_set: bool,
    description_is_set: bool,
) -> None:
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

    policy = vyos::PolicyRoute(
        host = r1,
        name = "T2",
        purged = {convert_bool(purge)}
    )

    vyos::PolicyRouteRule(
        policy = policy,
        id = 1,
        table = 2,
        %s
    )
            """
            % ",".join(
                line
                for line in [
                    "match_source_address = '192.168.100.104/29'"
                    if source_a_is_set
                    else None,
                    "match_destination_address = '192.168.2.2/29'"
                    if dest_a_is_set
                    else None,
                    "match_source_port = 123" if source_p_is_set else None,
                    "match_destination_port = 456" if dest_p_is_set else None,
                    "match_protocol = 'tcp'" if protocol_is_set else None,
                    "description = 'MyDescription'" if description_is_set else None,
                    # make sure trailing comma is added when at least one line present
                    "",
                ]
                if line is not None
            ),
        )

    make_config()

    assert project.get_resource(
        "vyos::Config"
    ).config.strip() == "policy route T2\n" + "\n".join(
        f"policy route T2 rule 1 {line}"
        for line in [
            "set table 2",
            "description MyDescription" if description_is_set else None,
            "source address 192.168.100.104/29" if source_a_is_set else None,
            "destination address 192.168.2.2/29" if dest_a_is_set else None,
            "source port 123" if source_p_is_set else None,
            "destination port 456" if dest_p_is_set else None,
            "protocol tcp" if protocol_is_set else None,
        ]
        if line is not None
    )

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


def test_41_policy_route_purge(project, vy_host, clear) -> None:
    def make_config(
        purge_iface: bool = False, purge_policy: bool = False, purge_rule: bool = False
    ) -> None:
        project.compile(
            f"""
    import vyos

    r1 = vyos::Host(
        name = "lab1",
        user = "vyos",
        password = "vyos",
        ip = "{vy_host}",
    )

    iface = vyos::Interface(
        host = r1,
        name = "eth1",
        address = "192.168.1.1/24",
        purged = {convert_bool(purge_iface)}
    )

    policy = vyos::PolicyRoute(
        host = r1,
        name = "T2",
        purged = {convert_bool(purge_policy)}
    )

    iface.policy_route = policy

    vyos::PolicyRouteRule(
        policy = policy,
        id = 1,
        table = 1,
        purged = {convert_bool(purge_rule)},
    )
            """,
        )

    make_config()
    project.deploy_resource("vyos::Config", node="policy route T2")
    project.deploy_resource("vyos::Config", node="interfaces ethernet eth1")

    # no assertions, just verify this doesn't fail
    # commented out due to inmanta/vyos#43
    # make_config(purge_rule=True)
    # project.deploy_resource("vyos::Config", node="policy route T2")

    # no assertions, just verify this doesn't fail
    make_config(purge_rule=True, purge_policy=True)
    project.deploy_resource("vyos::Config", node="interfaces ethernet eth1")
    project.deploy_resource("vyos::Config", node="policy route T2")

    # cleanup
    make_config(purge_rule=True, purge_policy=True, purge_iface=True)
    project.deploy_resource("vyos::Config", node="interfaces ethernet eth1")
    project.deploy_resource("vyos::Config", node="policy route T2")
