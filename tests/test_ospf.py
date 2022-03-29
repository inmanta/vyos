import vymgmt


def convert_bool(val):
    return "true" if val else "false"


def test_ospf(project, vy_host, console: vymgmt.Router):
    def make_config(purge=False):
        project.compile(
            f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    ospf1 = vyos::Ospf(
        area=0,
        network=["10.15.1.0/24"],
        router_id="10.1.1.1",
        host=r1,
        purged={convert_bool(purge)}
    )
        """
        )

    console.configure()
    console.run_conf_mode_command("load /config/clear.config")
    out = console.run_conf_mode_command("commit")
    print(out)

    console.exit(force=True)

    make_config()

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0

    make_config(True)

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0


def test_ospf_redistribute(project, vy_host, console: vymgmt.Router):
    def make_config(purge=False, redistributes="connected"):
        project.compile(
            f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    ospf1 = vyos::Ospf(
        area=0,
        network=["10.15.1.0/24"],
        router_id="10.1.1.1",
        host=r1,
        purged={convert_bool(purge)},
    )
    vyos::OspfRedistribute(
        type="{redistributes}",
        ospf=ospf1
    )
        """
        )

    console.configure()
    console.run_conf_mode_command("load /config/clear.config")
    out = console.run_conf_mode_command("commit")
    print(out)

    console.exit(force=True)

    make_config()

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0

    make_config(redistributes="static")
    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 2
    assert "protocols ospf redistribute connected metric-type" in compare
    assert "protocols ospf redistribute static metric-type" in compare

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0

    make_config(True)

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0
