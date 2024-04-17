import pytest
import os


@pytest.mark.integ_wf_emorep
def test_BuildEmorep(fixt_wf_emorep):
    # Check sourcedata validation
    assert fixt_wf_emorep.chk_pass

    # Run emorep integration tests
    emorep_test_status = pytest.main(["--pyargs", "-vv", "-m integ_emorep"])
    assert 0 == emorep_test_status


@pytest.mark.integ_wf_nki
def test_build_nki_files(fixt_wf_nki):
    raw_dict = fixt_wf_nki.raw_dict
    assert 2 == len(raw_dict.keys())
    assert ["sub-28522", "sub-58130"] == list(raw_dict.keys())
    assert os.path.exists(
        os.path.join(fixt_wf_nki.raw_path, "dataset_description.json")
    )
    assert 2 == len(raw_dict["sub-28522"])
    assert 5 == len(raw_dict["sub-58130"])


@pytest.mark.integ_wf_nki
def test_build_nki_names(fixt_wf_nki):
    raw_dict = fixt_wf_nki.raw_dict

    # Check dir path
    file_path = raw_dict["sub-58130"][3]
    part_path = file_path.split("build_rawdata/")[1]
    par_dir, raw_dir, subj_dir, sess_dir, type_dir, file_name = (
        part_path.split("/")
    )
    assert "data_mri_BIDS" == par_dir
    assert "rawdata" == raw_dir
    assert "sub-58130" == subj_dir
    assert "ses-BAS1" == sess_dir
    assert "func" == type_dir

    # Check file name
    subj, sess, task, run, acq, suff = file_name.split("_")
    assert "sub-58130" == subj
    assert "ses-BAS1" == sess
    assert "task-rest" == task
    assert "run-01" == run
    assert "acq-645" == acq
    assert "bold.nii.gz" == suff
