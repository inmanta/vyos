"""
   Copyright 2019-2022 Inmanta nv

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import netaddr
from inmanta.agent import handler


def convert_bool(val):
    return "true" if val else "false"


def test_ip_fact(project, vyos):
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


def test_ip_fact_multi(project, vyos):
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
