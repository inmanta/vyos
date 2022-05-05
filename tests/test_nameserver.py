def convert_bool(val):
    return "true" if val else "false"


def test_nameserver(project, vy_host, clear):
    def make_config(purge=False):
        project.compile(
            f"""
    import vyos

    r1 = vyos::Host(
        name="r1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    vyos::NameServer(
        host=r1,
        address="1.1.1.1",
        purged={convert_bool(purge)},
    )
    """
        )

    make_config()

    # pre create
    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert "system name-server 1.1.1.1" in project.get_resource(
        "vyos::Config"
    ).config.split("\n")
    assert len(compare) == 1

    # create
    project.deploy_resource("vyos::Config")
    compare = project.dryrun_resource("vyos::Config")
    assert not compare

    # stage delete
    make_config(True)

    # pre delete
    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    # do delete
    project.deploy_resource("vyos::Config")

    # post delete
    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0
