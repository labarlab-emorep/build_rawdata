import os
import pytest
import json
import glob
import nibabel as nib
from build_rawdata.resources import bidsify


@pytest.mark.dcm_bids
def test_BidsifyNii_bids_nii_struct(fixt_setup, fixt_bids_nii):
    for chk_dir in ["fmap", "func", "anat"]:
        assert os.path.exists(os.path.join(fixt_bids_nii.subj_raw, chk_dir))


@pytest.mark.dcm_bids
def test_BidsifyNii_bids_anat_data(fixt_setup, fixt_bids_nii):
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
def test_BidsifyNii_bids_func_struct(fixt_setup, fixt_bids_nii):
    search_path = os.path.join(fixt_bids_nii.subj_raw, "func")
    for chk_task in [fixt_setup.task, "task-rest"]:
        task_path = glob.glob(f"{search_path}/*{chk_task}*_bold.nii.gz")[0]
        subj, sess, task, run, suff = os.path.basename(task_path).split("_")
        assert subj == fixt_setup.subj
        assert sess == fixt_setup.sess
        assert task == chk_task
        assert run == fixt_setup.run
        assert suff == "bold.nii.gz"


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
