import os
import pytest
import json
import glob
import nibabel as nib
from build_rawdata.resources import bidsify


@pytest.mark.dcm_bids
def test_BidsifyNii_bids_nii_struct(fixt_setup, fixt_bids_nii):
    # Check for BIDS nesting structure
    for chk_dir in ["fmap", "func", "anat"]:
        assert os.path.exists(os.path.join(fixt_bids_nii.subj_raw, chk_dir))


@pytest.mark.dcm_bids
def test_BidsifyNii_bids_nii_anat(fixt_setup, fixt_bids_nii):
    anat_path = fixt_bids_nii.anat_list[0]

    # Anat name
    subj, sess, suff = os.path.basename(anat_path).split("_")
    assert subj == fixt_setup.subj
    assert sess == fixt_setup.sess
    assert "T1w.nii.gz" == suff

    # Anat data
    ref_anat = os.path.join(
        fixt_setup.proj_dir,
        "rawdata",
        fixt_setup.subj,
        fixt_setup.sess,
        "anat",
        f"{fixt_setup.subj}_{fixt_setup.sess}_T1w.nii.gz",
    )
    ref_img = nib.load(ref_anat)
    ref_data = ref_img.get_fdata()
    tst_img = nib.load(anat_path)
    tst_data = tst_img.get_fdata()
    assert (ref_data == tst_data).all()

    # Json sidecar
    assert os.path.exists(anat_path.replace(".nii.gz", ".json"))


@pytest.mark.dcm_bids
def test_BidsifyNii_bids_nii_func(fixt_setup, fixt_bids_nii):
    # Check func for BIDS naming structure
    search_path = os.path.join(fixt_bids_nii.subj_raw, "func")
    for chk_task in [fixt_setup.task, "task-rest"]:
        task_path = glob.glob(f"{search_path}/*{chk_task}*_bold.nii.gz")[0]
        subj, sess, task, run, suff = os.path.basename(task_path).split("_")
        assert subj == fixt_setup.subj
        assert sess == fixt_setup.sess
        assert task == chk_task
        assert run == fixt_setup.run
        assert suff == "bold.nii.gz"


@pytest.mark.dcm_bids
def test_BidsifyNii_update_func(fixt_setup, fixt_bids_nii):
    # Check for udpate to func json sidecar
    assert 2 == len(fixt_bids_nii.func_json)
    for json_path in fixt_bids_nii.func_json:
        with open(json_path) as jf:
            json_dict = json.load(jf)
        assert json_dict["TaskName"] in ["rest", fixt_setup.taskid]


@pytest.mark.dcm_bids
def test_BidsifyNii_update_fmap(fixt_bids_nii):
    # Check for udpate to fmap json sidecar
    assert 1 == len(fixt_bids_nii.fmap_json)
    with open(fixt_bids_nii.fmap_json[0]) as jf:
        json_dict = json.load(jf)
    assert "IntendedFor" in json_dict.keys()
    assert 2 == len(json_dict["IntendedFor"])


@pytest.mark.dcm_bids
def test_BidsifyNii_update_json(fixt_bids_nii):
    fmap_json = fixt_bids_nii.fmap_json[0]
    fixt_bids_nii.bids_nii._update_json(fmap_json, "Foo", "Bar")
    with open(fmap_json) as jf:
        json_dict = json.load(jf)
    assert "Bar" == json_dict["Foo"]


@pytest.mark.dcm_bids
def test_BidsifyNii_switch_name(fixt_setup, fixt_bids_nii):
    base_str = f"{fixt_setup.subj}_{fixt_setup.sess}"

    # Get output fuples
    anat_out = fixt_bids_nii.bids_nii._switch_name("DICOM_EmoRep_anat")
    task_out = fixt_bids_nii.bids_nii._switch_name(
        f"DICOM_EmoRep_run{fixt_setup.runid}", run=fixt_setup.runid
    )
    rest_out = fixt_bids_nii.bids_nii._switch_name(
        f"DICOM_Rest_run{fixt_setup.runid}", run=fixt_setup.runid
    )
    fmap_out = fixt_bids_nii.bids_nii._switch_name("DICOM_Field_Map_P_A")
    fmap_out1 = fixt_bids_nii.bids_nii._switch_name(
        "DICOM_Field_Map_P_A_run1", run=fixt_setup.runid
    )
    fmap_out2 = fixt_bids_nii.bids_nii._switch_name(
        "DICOM_Field_Map_P_A_run_2", run=fixt_setup.runid
    )

    # Validate tuple values
    assert ("anat", f"{base_str}_T1w") == anat_out
    assert (
        "func",
        f"{base_str}_{fixt_setup.task}_{fixt_setup.run}_bold",
    ) == task_out
    assert ("func", f"{base_str}_task-rest_{fixt_setup.run}_bold") == rest_out
    assert ("fmap", f"{base_str}_acq-rpe_dir-PA_epi") == fmap_out
    assert (
        "fmap",
        f"{base_str}_acq-rpe_dir-PA_{fixt_setup.run}_epi",
    ) == fmap_out1
    assert (
        "fmap",
        f"{base_str}_acq-rpe_dir-PA_{fixt_setup.run}_epi",
    ) == fmap_out2


def test_bidsify_exp(fixt_setup):
    # Test files are written to expected location
    raw_dir = os.path.join(fixt_setup.test_dir, "rawdata")
    file_desc, file_readme, file_ignore = bidsify.bidsify_exp(raw_dir)
    assert os.path.exists(os.path.join(raw_dir, "dataset_description.json"))
    assert os.path.exists(os.path.join(raw_dir, "README"))
    assert os.path.exists(os.path.join(raw_dir, ".bidsignore"))

    # Test content of description
    with open(file_desc) as jf:
        desc_dict = json.load(jf)
    assert "EmoRep" == desc_dict["Name"]
    assert "1.7.0" == desc_dict["BIDSVersion"]
    assert ["1R01MH113238"] == desc_dict["Funding"]
