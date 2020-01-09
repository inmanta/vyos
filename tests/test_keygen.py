from inmanta.agent import handler


def convert_bool(val):
    return "true" if val else "false"


def test_keygen(project, vy_host, clear):
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

    vyos::vpn::KeyGen(host=r1)
        """
        )

    make_config()

    compare = project.dryrun_resource("vyos::vpn::KeyGen")
    assert "purged" in compare
    assert len(compare) == 1

    project.deploy_resource("vyos::vpn::KeyGen")

    compare = project.dryrun_resource("vyos::vpn::KeyGen")
    assert len(compare) == 0

    resource = project.get_resource("vyos::vpn::KeyGen")
    myhandler = project.get_handler(resource, False)
    ctx = handler.HandlerContext(resource)
    facts = myhandler.facts(ctx, resource)
    assert "key" in facts
    assert len(facts["key"]) > 5
