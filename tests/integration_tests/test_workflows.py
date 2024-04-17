import pytest


@pytest.mark.integ_workflow
def test_BuildEmorep(fixt_workflow_emorep):
    # Check sourcedata validation
    assert fixt_workflow_emorep.chk_pass

    # Run emorep integration tests
    emorep_test_status = pytest.main(["--pyargs", "-vv", "-m integ_emorep"])
    assert 0 == emorep_test_status


@pytest.mark.integ_workflow
def test_build_nki():
    pass
