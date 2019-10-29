import pytest 

def test_smp_affinity(project):
    project.compile(f"""
import vyos

entity Tester:
    vyos::smp_affinity value
end

implement Tester using std::none

Tester(value="123")
Tester(value="auto")
Tester(value="cafebabe266")
Tester(value="cafebabe266,136")
""")

    with pytest.raises(Exception):

        project.compile(f"""
    import vyos

    entity Tester:
        vyos::smp_affinity value
    end

    implement Tester using std::none

    Tester(value="abdz")
    """)

def test_speed(project):
    project.compile(f"""
import vyos

entity Tester:
    vyos::speed value
end

implement Tester using std::none

Tester(value="10")
Tester(value="auto")
Tester(value="2500")
""")

    with pytest.raises(Exception):

        project.compile(f"""
    import vyos

    entity Tester:
        vyos::speed value
    end

    implement Tester using std::none

    Tester(value="75")
    """)