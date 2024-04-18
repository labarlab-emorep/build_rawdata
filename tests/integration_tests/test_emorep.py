import pytest
import os
import glob


@pytest.mark.integ_emorep
def test_ProcessMri_dcm_org(fixt_emorep_setup, fixt_emorep_mri):
    for chk_dir in [
        "EmoRep_anat",
        "EmoRep_run01",
        "Field_Map_PA",
        "Rest_run01",
    ]:
        assert os.path.exists(
            os.path.join(fixt_emorep_setup.dcm_path, chk_dir)
        )
    srch_path = os.path.join(
        fixt_emorep_setup.dcm_path, "20220429.ER0009.ER0009"
    )
    found_dcm = glob.glob(f"{srch_path}/*dcm")
    assert not found_dcm


@pytest.mark.integ_emorep
def test_ProcessMri_file_lists(fixt_emorep_mri):
    # Account for whether test was executed from integ_emorep
    # or integ_workflow.
    if isinstance(fixt_emorep_mri.cont_pipe, list):
        assert 4 == len(fixt_emorep_mri.cont_pipe)
        assert 1 == len(fixt_emorep_mri.anat_list)
    else:
        assert fixt_emorep_mri.cont_pipe
        assert not fixt_emorep_mri.anat_list
    assert 1 == len(fixt_emorep_mri.deface_path)


@pytest.mark.integ_emorep
def test_ProcessMri_bidsify(fixt_emorep_mri):
    # Account for whether test was executed from integ_emorep
    # or integ_workflow.
    if isinstance(fixt_emorep_mri.cont_pipe, list):
        chk_dcm_file = fixt_emorep_mri.cont_pipe[0]
        assert "DICOM" == os.path.basename(chk_dcm_file).split("_")[0]
        assert not os.path.exists(chk_dcm_file)
        chk_bids_file = fixt_emorep_mri.anat_list[0]
        assert os.path.exists(chk_bids_file)
    else:
        assert fixt_emorep_mri.cont_pipe
        assert not fixt_emorep_mri.anat_list


@pytest.mark.integ_emorep
def test_ProcessMri_deface(fixt_setup, fixt_emorep_mri):
    path_part = fixt_emorep_mri.deface_path[0].split("derivatives/")[1]
    deriv_dir, subj, sess, file_name = path_part.split("/")
    assert "deface" == deriv_dir
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess

    subj, sess, data_id, suff = file_name.split("_")
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess
    assert "T1w" == data_id
    assert "defaced" == suff.split(".")[0]


@pytest.mark.integ_emorep
def test_ProcessBeh_bidsify(fixt_setup, fixt_emorep_beh):
    assert "func" == os.path.basename(
        os.path.dirname(fixt_emorep_beh.tsv_path)
    )
    assert "func" == os.path.basename(
        os.path.dirname(fixt_emorep_beh.json_path)
    )


@pytest.mark.integ_emorep
def test_ProcessRate(fixt_setup, fixt_emorep_rest):
    path_part = fixt_emorep_rest.rest_path.split("rawdata_integ/")[1]
    subj, sess, data_type, file_name = path_part.split("/")
    assert "beh" == data_type
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess

    subj, sess, task, suff = file_name.split("_")
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess
    assert "rest-ratings" == task
    assert "2022-04-28" == suff.split(".")[0]


@pytest.mark.integ_emorep
def test_ProcessPhys_data(fixt_setup, fixt_emorep_phys):
    assert 0.012512 == fixt_emorep_phys.df.at[0, 0]
    assert -0.28717 == fixt_emorep_phys.df.at[0, 1]
    assert 0.337219 == fixt_emorep_phys.df.at[0, 2]
    assert 5.0 == fixt_emorep_phys.df.at[0, 3]
    assert 255.0 == fixt_emorep_phys.df.at[0, 11]
    assert -0.28717 == fixt_emorep_phys.df.at[0, 12]


@pytest.mark.integ_emorep
def test_ProcessPhys_bidsify(fixt_setup, fixt_emorep_phys):
    path_part = fixt_emorep_phys.phys_path.split("rawdata_integ/")[1]
    subj, sess, data_type, file_name = path_part.split("/")
    assert "phys" == data_type
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess

    subj, sess, task, run, rec, suff = file_name.split("_")
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess
    assert task == fixt_setup.task
    assert "recording-biopack" == rec
    assert "physio" == suff.split(".")[0]
