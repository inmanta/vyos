def convert_bool(val):
    return "true" if val else "false"

def test_interface_basic(project, vy_host, clear):
    def make_config(purge=False):
        project.compile(f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        address="192.168.5.3/24",
        purged={convert_bool(purge)},
    )
    """)


    make_config()

    # pre create
    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
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

def test_interface_and_vif(project, vy_host, clear):
    def make_config(purge=False):
        project.compile(f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        address="192.168.5.3/24",
        purged={convert_bool(purge)},
    )
    vif = vyos::Vif(parent=itf, vlan=10, host=r1)

    vif.addresses += vyos::Address(ip="192.168.7.3/24")
    vif.addresses += vyos::Address(ip="2a02:1810:bc04:5200::1/64")
    """)

    make_config()

    # pre create
    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    # create
    project.deploy_resource("vyos::Config")
    compare = project.dryrun_resource("vyos::Config")
    assert not compare

    def make_config_2(purge=False):
        project.compile(f"""
    import vyos

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        address="192.168.5.3/24",
        purged={convert_bool(purge)},
    )
    vif = vyos::Vif(parent=itf, vlan=10, host=r1)

    vif.addresses += vyos::Address(ip="192.168.7.3/24")
    """)

    make_config_2()

    # pre create
    compare = project.dryrun_resource("vyos::Config")
    assert "interfaces ethernet eth1 vif 10 address" in compare
    assert len(compare) == 1

    # create
    project.deploy_resource("vyos::Config")
    compare = project.dryrun_resource("vyos::Config")
    assert not compare

     # stage delete
    make_config_2(True)

    # pre delete
    compare = project.dryrun_resource("vyos::Config")
    assert "purged" in compare
    assert len(compare) == 1

    # do delete
    project.deploy_resource("vyos::Config")

    # post delete
    compare = project.dryrun_resource("vyos::Config")
    assert len(compare) == 0