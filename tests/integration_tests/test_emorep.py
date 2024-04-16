import pytest


@pytest.mark.integ
def test_ProcessMri(fixt_emorep_mri):
    # print(fixt_emorep_mri.cont_pipe)
    # print(fixt_emorep_mri.anat_list)
    # print(fixt_emorep_mri.deface_path)

    assert 4 == len(fixt_emorep_mri.cont_pipe)
    assert 1 == len(fixt_emorep_mri.anat_list)


@pytest.mark.integ
def test_ProcessBeh():
    pass


@pytest.mark.integ
def test_ProcessRate():
    pass


@pytest.mark.integ
def test_ProcessPhys():
    pass
