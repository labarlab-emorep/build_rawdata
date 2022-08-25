# %%
import pytest
import os
import glob
import shutil
from copy import deepcopy

try:
    from dcm_conversion.resources import process, bidsify, behavior
except ImportError:
    dcm_conversion = None


# %%
@pytest.fixture(scope="session")
def fixt_setup():
    # Hardcode variables for specific testing
    subid = "ER0009"
    sess = "ses-day2"
    task = "movies"
    proj_dir = "/mnt/keoki/experiments2/EmoRep/Emorep_BIDS"

    # Setup reference variables
    unit_dir = os.path.join(proj_dir, "code/unit_test")
    ref_dir = os.path.join(unit_dir, "ref_data")
    ref_t1w = os.path.join(ref_dir, "sub-ER0009_ses-day2_T1w.nii.gz")
    ref_deface = os.path.join(
        ref_dir, "sub-ER0009_ses-day2_T1w_defaced.nii.gz"
    )
    ref_beh_tsv = os.path.join(
        ref_dir, "sub-ER0009_ses-day2_task-movies_run-01_events.tsv"
    )
    ref_beh_json = os.path.join(
        ref_dir, "sub-ER0009_ses-day2_task-movies_run-01_events.json"
    )

    # Setup test variables
    test_subj = os.path.join(unit_dir, f"sub-{subid}")
    test_subj_sess = os.path.join(test_subj, sess)

    return {
        "subid": subid,
        "sess": sess,
        "task": task,
        "proj_dir": proj_dir,
        "unit_dir": unit_dir,
        "ref_t1w": ref_t1w,
        "ref_deface": ref_deface,
        "ref_beh_tsv": ref_beh_tsv,
        "ref_beh_json": ref_beh_json,
        "test_subj": test_subj,
        "test_subj_sess": test_subj_sess,
    }


# %%
@pytest.fixture(scope="session")
def fixt_dcm_bids(fixt_setup):
    # Make output dir
    out_dir = fixt_setup["test_subj_sess"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Find dicom dir
    source_subj = os.path.join(
        fixt_setup["proj_dir"], "sourcedata", fixt_setup["subid"]
    )
    dcm_dir = sorted(glob.glob(f"{source_subj}/day*/DICOM"))[0]

    # Conduct dcm2niix, bidsify
    nii_list, json_list = process.dcm2niix(
        dcm_dir,
        out_dir,
        fixt_setup["subid"],
        fixt_setup["sess"],
        fixt_setup["task"],
    )
    t1_list = bidsify.bidsify_nii(
        nii_list,
        json_list,
        out_dir,
        fixt_setup["subid"],
        fixt_setup["sess"],
        fixt_setup["task"],
    )

    # Update fixt_setup as new dict
    dcm2niix_dict = deepcopy(fixt_setup)
    h_dict = {
        "nii_list": nii_list,
        "json_list": json_list,
        "test_t1w": t1_list[0],
    }
    dcm2niix_dict.update(h_dict)

    # Yield dict and teardown
    yield dcm2niix_dict
    shutil.rmtree(os.path.dirname(out_dir))


# %%
@pytest.fixture(scope="function")
def fixt_deface(fixt_setup):
    # Execute deface method
    process.deface(
        [fixt_setup["ref_t1w"]],
        fixt_setup["unit_dir"],
        fixt_setup["subid"],
        fixt_setup["sess"],
    )

    # Get output of process.deface
    out_dir = os.path.join(
        fixt_setup["unit_dir"],
        "deface",
        f"sub-{fixt_setup['subid']}",
        fixt_setup["sess"],
    )
    deface_file = glob.glob(f"{out_dir}/*defaced.nii.gz")[0]

    # Update dictionary
    deface_dict = deepcopy(fixt_setup)
    h_dict = {"test_deface": deface_file}
    deface_dict.update(h_dict)

    # Yield dict and teardown
    yield deface_dict
    shutil.rmtree(os.path.join(fixt_setup["unit_dir"], "deface"))


@pytest.fixture(scope="function")
def fixt_exp_bids(fixt_setup):
    # Execute bidisfy method
    out_dir = fixt_setup["test_subj"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    bidsify.bidsify_exp(out_dir)

    # Make paths to output
    data_desc = os.path.join(out_dir, "dataset_description.json")
    read_me = os.path.join(out_dir, "README")
    ignore_file = os.path.join(out_dir, ".bidsignore")

    # Update dict
    bids_dict = deepcopy(fixt_setup)
    h_dict = {
        "data_desc": data_desc,
        "read_me": read_me,
        "ignore_file": ignore_file,
    }
    bids_dict.update(h_dict)

    # Yield and teardown
    yield bids_dict
    shutil.rmtree(out_dir)


@pytest.fixture(scope="module")
def fixt_behavior(fixt_setup):
    # Make out_dir
    out_dir = fixt_setup["test_subj"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Find source csv
    source_subj = os.path.join(
        fixt_setup["proj_dir"], "sourcedata", fixt_setup["subid"]
    )
    task_file = sorted(
        glob.glob(f"{source_subj}/day*/Scanner_behav/*run-1*csv")
    )[0]

    # Execute behavior.events method
    behavior.events(
        task_file,
        out_dir,
        fixt_setup["subid"],
        fixt_setup["sess"],
        f"task-{fixt_setup['task']}",
        "run-01",
    )

    # Add outputs to fixt dict
    events_tsv = os.path.join(
        out_dir, "sub-ER0009_ses-day2_task-movies_run-01_events.tsv"
    )
    events_json = os.path.join(
        out_dir, "sub-ER0009_ses-day2_task-movies_run-01_events.json"
    )
    beh_dict = deepcopy(fixt_setup)
    h_dict = {
        "events_tsv": events_tsv,
        "events_json": events_json,
    }
    beh_dict.update(h_dict)

    # Yield and teardown
    yield beh_dict
    shutil.rmtree(out_dir)
