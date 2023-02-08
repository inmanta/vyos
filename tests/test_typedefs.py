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
import pytest


def test_speed(project):
    project.compile(
        """
import vyos

entity Tester:
    vyos::speed value
end

implement Tester using std::none

Tester(value="10")
Tester(value="auto")
Tester(value="2500")
"""
    )

    with pytest.raises(Exception):
        project.compile(
            """
    import vyos

    entity Tester:
        vyos::speed value
    end

    implement Tester using std::none

    Tester(value="75")
    """
        )
