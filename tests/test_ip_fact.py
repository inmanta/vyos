import netaddr
from inmanta.agent import handler


def convert_bool(val):
    return "true" if val else "false"


def test_ip_fact(project, vy_host, clear):
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

    itf = vyos::Interface(
        host=r1,
        name="eth0",
        purged={convert_bool(purge)},
    )

    vyos::IpFact(interface=itf)
    """
        )

    make_config()

    resource = project.get_resource("vyos::IpFact")
    myhandler = project.get_handler(resource, False)
    ctx = handler.HandlerContext(resource)
    facts = myhandler.facts(ctx, resource)
    assert "ip_address" in facts
    netaddr.IPNetwork(facts["ip_address"])


def test_ip_fact_multi(project, vy_host, clear):
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

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        purged={convert_bool(purge)},
        addresses = [
            vyos::Address(ip="169.254.0.1/24"),
            vyos::Address(ip="169.254.0.2/24")
        ]
    )


    vyos::IpFact(interface=itf)
    """
        )

    make_config()

    project.deploy_resource("vyos::Config")

    resource = project.get_resource("vyos::IpFact")
    myhandler = project.get_handler(resource, False)
    ctx = handler.HandlerContext(resource)
    facts = myhandler.facts(ctx, resource)
    assert "ip_address" in facts
    netaddr.IPNetwork(facts["ip_address"])
    assert "ip_address_0" in facts
    netaddr.IPNetwork(facts["ip_address_0"])
    assert "ip_address_1" in facts
    netaddr.IPNetwork(facts["ip_address_1"])
