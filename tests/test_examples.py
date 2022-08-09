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
