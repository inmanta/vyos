import pytest


def test_speed(project):
    project.compile(
        f"""
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
            f"""
    import vyos

    entity Tester:
        vyos::speed value
    end

    implement Tester using std::none

    Tester(value="75")
    """
        )
