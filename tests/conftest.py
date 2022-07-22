"""Generate fixtures.

Make fixtures used by test_convert, test_process.
Written for labaserv2, keoki environment.
"""
import pytest
import os
import glob
import shutil

try:
    from dcm_conversion import process, bidsify
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

    return {
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


@pytest.fixture(scope="session")
def ref_info(local_vars):
    # Execute convert methods, get outputs
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

    # Execute process method, get output
    process.deface(
        t1_list,
        local_vars["test_dir"],
        local_vars["subid"],
        local_vars["sess"],
    )
    test_deface = sorted(
        glob.glob(
            f"{local_vars['test_dir']}/deface/**/*defaced.nii.gz",
            recursive=True,
        )
    )

    # Update local_vars as new dict
    fixt_dict = local_vars
    test_dict = {
        "nii_list": nii_list,
        "json_list": json_list,
        "test_t1w": t1_list[0],
        "test_deface": test_deface[0],
    }
    fixt_dict.update(test_dict)

    # Supply dict values while testing, then clean
    yield fixt_dict
    shutil.rmtree(os.path.dirname(local_vars["test_raw"]))
    shutil.rmtree(os.path.join(local_vars["test_dir"], "deface"))
