import os


def load_example(example, ip):
    path = os.path.join(os.path.dirname(__file__), f"../examples/{example}.cf")
    with open(path, mode="r") as fh:
        return fh.read().replace('mgmt_ip = "x.x.x.x"', f'mgmt_ip = "{ip}"')


def test_example_interfaces(project, vyos):
    project.compile(load_example("interfaces", vyos.router_ip))
    project.deploy_all().assert_all()


def test_example_ospf(project, vyos):
    project.compile(load_example("ospf", vyos.router_ip))
    project.deploy_all().assert_all()


def test_example_bridge_gre(project, vyos):
    project.compile(load_example("gre_bridge", vyos.router_ip))
    project.deploy_all().assert_all()
