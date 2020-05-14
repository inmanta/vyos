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


def test_policy_route(project, vy_host, clear):
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
        source_address = "192.168.100.104/29",
        protocol = "tcp",
        description = "my description",
        purged = {convert_bool(purge)}
    )
            """,
        )

    make_config()

    compare = project.dryrun_resource("vyos::Config")
    assert "policy route T2 rule 1 set table" in compare
    assert "policy route T2 rule 1 source address" in compare
    assert "policy route T2 rule 1 destination address" in compare
    assert "policy route T2 rule 1 protocol" in compare
    assert "policy route T2 rule 1 description" in compare
    assert "purged" in compare
    assert len(compare) == 6

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
