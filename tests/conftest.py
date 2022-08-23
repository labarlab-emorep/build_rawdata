"""Generate fixtures.

Make fixtures used by test_convert, test_process.
Written for labaserv2, keoki environment.
"""
import pytest
import os
import glob
import shutil

try:
    from dcm_conversion.resources import process, bidsify
except ImportError:
    dcm_conversion = None


@pytest.fixture(scope="session")
def local_vars():
    # Hardcode variables for specific testing
    subid = "ER0009"
    sess = "ses-day2"
    task = "movies"
    source_path = "/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/sourcedata"

    # Setup paths
    test_dir = os.path.join(os.path.dirname(source_path), "code/unit_test")
    ref_dir = os.path.join(test_dir, "ref_data")
    ref_t1w = os.path.join(ref_dir, "sub-ER0009_ses-day2_T1w.nii.gz")
    ref_deface = os.path.join(
        ref_dir, "sub-ER0009_ses-day2_T1w_defaced.nii.gz"
    )
    test_raw = os.path.join(test_dir, f"sub-{subid}", sess)
    dcm_dirs = sorted(glob.glob(f"{source_path}/{subid}/day*/DICOM"))
    subj_source = dcm_dirs[0]

    # Make output dir
    if not os.path.exists(test_raw):
        os.makedirs(test_raw)

    # Yield, then teardown all
    yield {
        "subid": subid,
        "sess": sess,
        "task": task,
        "subj_source": subj_source,
        "test_dir": test_dir,
        "test_raw": test_raw,
        "ref_dir": ref_dir,
        "ref_t1w": ref_t1w,
        "ref_deface": ref_deface,
    }
    shutil.rmtree(os.path.dirname(test_raw))


@pytest.fixture(scope="package")
def info_dcm_bids(local_vars):
    # Conduct dcm2niix, bidsify
    nii_list, json_list = process.dcm2niix(
        local_vars["subj_source"],
        local_vars["test_raw"],
        local_vars["subid"],
        local_vars["sess"],
        local_vars["task"],
    )
    t1_list = bidsify.bidsify_nii(
        nii_list,
        json_list,
        local_vars["test_raw"],
        local_vars["subid"],
        local_vars["sess"],
        local_vars["task"],
    )

    # Update local_vars as new dict
    dcm2niix_dict = local_vars
    h_dict = {
        "nii_list": nii_list,
        "json_list": json_list,
        "test_t1w": t1_list[0],
    }
    dcm2niix_dict.update(h_dict)

    # Supply dict values while testing
    yield dcm2niix_dict


@pytest.fixture(scope="function")
def info_deface(local_vars):
    # Execute deface method
    process.deface(
        [local_vars["ref_t1w"]],
        local_vars["test_dir"],
        local_vars["subid"],
        local_vars["sess"],
    )

    # Get output of process.deface
    out_dir = os.path.join(
        local_vars["test_dir"],
        "deface",
        f"sub-{local_vars['subid']}",
        local_vars["sess"],
    )
    deface_file = glob.glob(f"{out_dir}/*defaced.nii.gz")[0]

    # Update dictionary
    deface_dict = local_vars
    h_dict = {"test_deface": deface_file}
    deface_dict.update(h_dict)

    # Supply while testing
    yield deface_dict
    shutil.rmtree(os.path.join(local_vars["test_dir"], "deface"))
