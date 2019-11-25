import vymgmt

def convert_bool(val):
    return "true" if val else "false"

def test_ospf(project, vy_host, clear):
    def make_config(purge=False):
        project.compile(f"""
    import vyos 
    import vyos::vpn

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    vyos::vpn::KeyGen(host=r1)
        """)


    make_config()
    
    compare = project.dryrun_resource("vyos::vpn::KeyGen")
    assert "purged" in compare
    assert len(compare) == 1
    
    # project.deploy_resource("vyos::Config")

    # compare = project.dryrun_resource("vyos::Config")
    # assert len(compare) == 0

    # make_config(True)

    # compare = project.dryrun_resource("vyos::Config")
    # assert "purged" in compare
    # assert len(compare) == 1

    # project.deploy_resource("vyos::Config")

    # compare = project.dryrun_resource("vyos::Config")
    # assert len(compare) == 0

