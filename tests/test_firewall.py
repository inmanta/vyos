import inmanta


def test_firewall(project, vy_host, clear):
    project.compile(
        f"""
    import vyos
    import vyos::firewall

    r1 = vyos::Host(
        name="lab1",
        user="vyos",
        password="vyos",
        ip="{vy_host}")

    itf = vyos::Interface(
        host=r1,
        name="eth1",
        address="192.168.5.3/24",
        inbound_ruleset=ruleset_1,
        outbound_ruleset=ruleset_1
    )

    ruleset_1 = vyos::firewall::RuleSet(
        host=r1,
        name="test-set-1",
        default_action="accept",
    )

    a_group = vyos::firewall::AddressGroup(
        host=r1,
        name="test-a-group",
        addresses=["192.168.25.6", "192.168.26.8-192.168.26.10"]
    )

    n_group = vyos::firewall::NetworkGroup(
        host=r1,
        name="test-n-group",
        networks=["192.168.27.0/24"]
    )

    p_group = vyos::firewall::PortGroup(
        host=r1,
        name="test-p-group",
        ports=["22", "80", "443"]
    )

    rule_1 = vyos::firewall::Rule(
        id=10,
        action="accept",
        protocol="icmp",
        ruleset=ruleset_1
    )

    rule_2 = vyos::firewall::Rule(
        id=20,
        action="accept",
        protocol="tcp",
        source=[a_group, p_group],
        destination=[n_group, p_group],
        ruleset=ruleset_1
    )
    """
    )

    # address group
    a_group = project.get_resource(
        "vyos::Config", node="firewall group address-group test-a-group"
    )
    assert a_group

    a_group_cfg = a_group.config.splitlines()
    assert len(a_group_cfg) == 3
    assert (
        "firewall group address-group test-a-group address 192.168.25.6" in a_group_cfg
    )
    assert (
        "firewall group address-group test-a-group address 192.168.26.8-192.168.26.10"
        in a_group_cfg
    )
    assert (
        'firewall group address-group test-a-group description "inmanta managed address-group"'
        in a_group_cfg
    )

    a_group_deploy = project.deploy(a_group)
    assert a_group_deploy.status == inmanta.const.ResourceState.deployed

    # network group
    n_group = project.get_resource(
        "vyos::Config", node="firewall group network-group test-n-group"
    )
    assert n_group

    n_group_cfg = n_group.config.splitlines()
    assert len(n_group_cfg) == 2
    assert (
        "firewall group network-group test-n-group network 192.168.27.0/24"
        in n_group_cfg
    )
    assert (
        'firewall group network-group test-n-group description "inmanta managed network-group"'
        in n_group_cfg
    )

    n_group_deploy = project.deploy(n_group)
    assert n_group_deploy.status == inmanta.const.ResourceState.deployed

    # port group
    p_group = project.get_resource(
        "vyos::Config", node="firewall group port-group test-p-group"
    )
    assert p_group

    p_group_cfg = p_group.config.splitlines()
    assert len(p_group_cfg) == 4
    assert "firewall group port-group test-p-group port 22" in p_group_cfg
    assert "firewall group port-group test-p-group port 80" in p_group_cfg
    assert "firewall group port-group test-p-group port 443" in p_group_cfg
    assert (
        'firewall group port-group test-p-group description "inmanta managed port-group"'
        in p_group_cfg
    )

    p_group_deploy = project.deploy(p_group)
    assert p_group_deploy.status == inmanta.const.ResourceState.deployed

    # ruleset
    ruleset = project.get_resource("vyos::Config", node="firewall name test-set-1")
    assert ruleset

    ruleset_cfg = ruleset.config
    assert "firewall name test-set-1 default-action accept" in ruleset_cfg
    assert (
        'firewall name test-set-1 description "inmanta managed ruleset"' in ruleset_cfg
    )
    assert "firewall name test-set-1 rule 10 action accept" in ruleset_cfg
    assert "firewall name test-set-1 rule 10 protocol icmp" in ruleset_cfg
    assert (
        'firewall name test-set-1 rule 10 description "inmanta managed rule"'
        in ruleset_cfg
    )
    assert "firewall name test-set-1 rule 20 action accept" in ruleset_cfg
    assert "firewall name test-set-1 rule 20 protocol tcp" in ruleset_cfg
    assert (
        'firewall name test-set-1 rule 20 description "inmanta managed rule"'
        in ruleset_cfg
    )
    assert (
        "firewall name test-set-1 rule 20 source group address-group test-a-group"
        in ruleset_cfg
    )
    assert (
        "firewall name test-set-1 rule 20 source group port-group test-p-group"
        in ruleset_cfg
    )
    assert (
        "firewall name test-set-1 rule 20 destination group network-group test-n-group"
        in ruleset_cfg
    )
    assert (
        "firewall name test-set-1 rule 20 destination group port-group test-p-group"
        in ruleset_cfg
    )

    ruleset_deploy = project.deploy(ruleset)
    assert ruleset_deploy.status == inmanta.const.ResourceState.deployed

    # interface
    interface = project.get_resource("vyos::Config", node="interfaces ethernet eth1")
    assert interface

    interface_cfg = interface.config.splitlines()
    assert "interfaces ethernet eth1 address 192.168.5.3/24" in interface_cfg
    assert "interfaces ethernet eth1 duplex auto" in interface_cfg
    assert "interfaces ethernet eth1 speed auto" in interface_cfg
    assert "interfaces ethernet eth1 firewall in name test-set-1" in interface_cfg
    assert "interfaces ethernet eth1 firewall out name test-set-1" in interface_cfg

    interface_deploy = project.deploy(interface)
    assert interface_deploy.status == inmanta.const.ResourceState.deployed
