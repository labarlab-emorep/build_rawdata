import pytest
import os
import shutil
import glob
from build_rawdata.resources import behavior
from build_rawdata.resources import process
from build_rawdata.resources import bidsify


class SupplyVars:
    pass


@pytest.fixture(scope="session")
def fixt_setup():
    """Yield setup resources."""
    # Start object for yielding
    obj_setup = SupplyVars()

    # Hardcode variables for specific testing
    obj_setup.subjid = "ER0009"
    obj_setup.sessid = "day3"
    obj_setup.runid = "01"
    obj_setup.taskid = "scenarios"
    obj_setup.subj = "sub-" + obj_setup.subjid
    obj_setup.sess = "ses-" + obj_setup.sessid
    obj_setup.task = "task-" + obj_setup.taskid
    obj_setup.run = "run-" + obj_setup.runid

    # Setup paths
    par_dir = "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
    obj_setup.proj_dir = os.path.join(par_dir, "data_scanner_BIDS")
    obj_setup.test_dir = os.path.join(par_dir, "code/unit_test/build_rawdata")
    obj_setup.subj_source = os.path.join(
        obj_setup.proj_dir,
        "sourcedata",
        obj_setup.subjid,
        f"{obj_setup.sessid}_{obj_setup.taskid}",
    )

    # Make testing output parent directories
    for _dir in ["rawdata", "derivatives"]:
        mk_dir = os.path.join(obj_setup.test_dir, _dir)
        if not os.path.exists(mk_dir):
            os.makedirs(mk_dir)

    # Yield and teardown
    yield obj_setup
    return  # TODO remove
    shutil.rmtree(obj_setup.test_dir)


@pytest.fixture(scope="session")
def fixt_behavior(fixt_setup):
    """Yield resources for testing behavior module."""
    obj_beh = SupplyVars()
    task_path = os.path.join(
        fixt_setup.subj_source,
        "Scanner_behav",
        f"emorep_scannertextData_{fixt_setup.subjid}_"
        + f"ses{fixt_setup.sessid}_run1_04282022.csv",
    )

    # Start obj for making events TSV
    obj_beh.ev_info = behavior._EventsData(task_path)

    # Get output from events_tsv
    subj_raw = os.path.join(
        fixt_setup.test_dir,
        "rawdata",
        fixt_setup.subj,
        fixt_setup.sess,
        "func",
    )
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    obj_beh.event_tsv, obj_beh.event_json = behavior.events_tsv(
        task_path,
        subj_raw,
        fixt_setup.subjid,
        fixt_setup.sess,
        fixt_setup.task,
        fixt_setup.run,
    )

    # Get output from rest_ratings
    rate_path = os.path.join(
        fixt_setup.subj_source,
        "Scanner_behav",
        f"emorep_RestRatingData_{fixt_setup.subj}_"
        + f"{fixt_setup.sess}_04282022.csv",
    )
    out_file = os.path.join(subj_raw, "tst_rest_ratings.tsv")
    obj_beh.df_rest = behavior.rest_ratings(
        rate_path, fixt_setup.subjid, fixt_setup.sess, out_file
    )

    yield obj_beh


@pytest.fixture(scope="session")
def fixt_dcm2nii(fixt_setup):
    """Yield resources for testing dcm2niix."""
    obj_dcm2nii = SupplyVars()

    # Copy some data to avoid building all niis
    test_source = os.path.join(
        fixt_setup.test_dir, "sourcedata", fixt_setup.subj, "DICOM"
    )
    if not os.path.exists(test_source):
        os.makedirs(test_source)
    chk_dcm = glob.glob(f"{test_source}/*dcm")
    if not chk_dcm:
        for cp_dir in [
            "EmoRep_anat",
            f"EmoRep_run{fixt_setup.runid}",
            "Rest_run01",
            "Field_Map_PA",
        ]:
            shutil.copytree(
                os.path.join(fixt_setup.subj_source, "DICOM", cp_dir),
                test_source,
                dirs_exist_ok=True,
            )

    # Build niis
    subj_raw = os.path.join(
        fixt_setup.test_dir, "rawdata", fixt_setup.subj, fixt_setup.sess
    )
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    obj_dcm2nii.raw_nii, obj_dcm2nii.raw_json = process.dcm2niix(
        test_source, subj_raw, fixt_setup.subjid
    )
    yield obj_dcm2nii


@pytest.fixture(scope="session")
def fixt_bids_nii(fixt_setup, fixt_dcm2nii):
    """Yield resources for testing BIDSifying of nii files."""
    obj_bids = SupplyVars()

    # Copy raw dc2nii output to avoid test conflicts, but only when
    # bidsification has not yet occurred.
    subj_raw = os.path.join(
        fixt_setup.test_dir, "rawdata_bids", fixt_setup.subj, fixt_setup.sess
    )
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    chk_file = os.path.join(
        subj_raw, "anat", f"{fixt_setup.subj}_{fixt_setup.sess}_T1w.nii.gz"
    )
    if not os.path.exists(chk_file):
        src_raw = os.path.join(
            fixt_setup.test_dir, "rawdata", fixt_setup.subj, fixt_setup.sess
        )
        shutil.copytree(src_raw, subj_raw, dirs_exist_ok=True)

    # Run bidsification
    bids_nii = bidsify.BidsifyNii(
        subj_raw, fixt_setup.subj, fixt_setup.sess, fixt_setup.task
    )
    obj_bids.subj_raw = subj_raw
    obj_bids.anat_list = bids_nii.bids_nii()
    obj_bids.func_json = bids_nii.update_func()
    obj_bids.fmap_json = bids_nii.update_fmap()
    yield obj_bids


@pytest.fixture(scope="session")
def fixt_deface(fixt_setup):
    """Yield resources for testing process.deface."""
    obj_deface = SupplyVars()

    # Get reference defaced file
    obj_deface.ref_deface = os.path.join(
        fixt_setup.proj_dir,
        "derivatives/deface",
        fixt_setup.subj,
        fixt_setup.sess,
        f"{fixt_setup.subj}_{fixt_setup.sess}_T1w_defaced.nii.gz",
    )

    # Deface anat file
    ref_anat_dir = os.path.join(
        fixt_setup.proj_dir,
        "rawdata",
        fixt_setup.subj,
        fixt_setup.sess,
        "anat",
    )
    t1_list = glob.glob(f"{ref_anat_dir}/*T1w.nii.gz")
    deface_list = process.deface(
        t1_list,
        os.path.join(fixt_setup.test_dir, "derivatives"),
        fixt_setup.subjid,
        fixt_setup.sess,
    )
    obj_deface.tst_deface = deface_list[0]
    yield obj_deface
