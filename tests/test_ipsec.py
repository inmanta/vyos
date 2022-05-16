import vymgmt


def convert_bool(val):
    return "true" if val else "false"


def test_ipsec_options(project, vyos):
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

    vyos::vpn::IPSECOptions(
        host=r1,
        purged={convert_bool(purge)},
        ipsec_interfaces=["eth1", "eth2"],
        nat_traversal=true,
        allowed_nat_networks=["192.168.10.0/24", ]
    )
        """
        )

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert not compare

    make_config(True)

    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::Config")

    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0
