import pytest
import os
import json


@pytest.mark.dcm_bids
def test_bids_nii(fixt_setup, fixt_dcm_bids):
    # Test anat_names
    ref_name = os.path.basename(fixt_setup["ref_t1w"])
    test_name = os.path.basename(fixt_dcm_bids["test_t1w"])
    assert ref_name == test_name

    # Test bids dir names
    unit_dirs = os.listdir(fixt_setup["test_subj_sess"])
    assert all(x in unit_dirs for x in ["anat", "func", "fmap"])

    # Test bids organization
    test_subj_sess = fixt_setup["test_subj_sess"]
    anat_list = os.listdir(f"{test_subj_sess}/anat")
    func_list = os.listdir(f"{test_subj_sess}/func")
    fmap_list = os.listdir(f"{test_subj_sess}/fmap")
    assert any("T1w" in x for x in anat_list)
    assert any("bold" in x for x in func_list)
    assert any("epi" in x for x in fmap_list)


@pytest.mark.dcm_bids
def test_fmap_update(fixt_setup):
    fmap_dir = os.path.join(fixt_setup["test_subj_sess"], "fmap")
    fmap_json = os.path.join(
        fmap_dir, "sub-ER0009_ses-day2_acq-rpe_dir-PA_epi.json"
    )
    assert os.path.exists(fmap_json)

    with open(fmap_json) as jf:
        fmap_dict = json.load(jf)
    assert fmap_dict.__contains__("IntendedFor")
    assert fmap_dict["IntendedFor"]


@pytest.mark.dcm_bids
def test_func_update(fixt_setup):
    func_dir = os.path.join(fixt_setup["test_subj_sess"], "func")
    func_json = os.path.join(
        func_dir, "sub-ER0009_ses-day2_task-movies_run-01_bold.json"
    )
    assert os.path.exists(func_json)

    with open(func_json) as jf:
        func_dict = json.load(jf)
    assert func_dict.__contains__("TaskName")
    assert func_dict["TaskName"] == fixt_setup["task"].split("-")[1]


def test_bidsify_exp(fixt_exp_bids):
    assert os.path.exists(fixt_exp_bids["data_desc"])
    assert os.path.exists(fixt_exp_bids["read_me"])
    assert os.path.exists(fixt_exp_bids["ignore_file"])
