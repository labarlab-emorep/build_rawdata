"""Unit testing of dcm_conversion.convert.

Written for labaserv2, keoki environment.
"""
# %%
import pytest
import os
import glob
import shutil
import nibabel as nib

try:
    from dcm_conversion import convert
except ImportError:
    dcm_conversion = None

# %%
@pytest.fixture(scope="module")
def local_vars():
    # hardcode certain vars
    subid = "ER0009"
    sess = "ses-day2"
    task = "movies"
    source_path = "/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/sourcedata"

    # setup paths
    test_dir = os.path.join(os.path.dirname(source_path), "code/unit_test")
    ref_dir = os.path.join(test_dir, "ref_data")
    ref_t1w = os.path.join(ref_dir, "sub-ER0009_ses-day2_T1w.nii.gz")
    test_raw = os.path.join(test_dir, f"sub-{subid}", sess)
    dcm_dirs = sorted(glob.glob(f"{source_path}/{subid}/day*/DICOM"))
    subj_source = dcm_dirs[0]

    if not os.path.exists(test_raw):
        os.makedirs(test_raw)

    return {
        "subid": subid,
        "sess": sess,
        "task": task,
        "subj_source": subj_source,
        "test_raw": test_raw,
        "ref_dir": ref_dir,
        "ref_t1w": ref_t1w,
    }


@pytest.fixture(scope="module")
def ref_info(local_vars):
    # Generate niis, update dict
    t1_list = convert.dcm2niix(
        local_vars["subj_source"],
        local_vars["test_raw"],
        local_vars["subid"],
        local_vars["sess"],
        local_vars["task"],
    )
    fixt_dict = local_vars
    test_dict = {"test_t1w": t1_list[0]}
    fixt_dict.update(test_dict)

    # Supply dict values while testing, then clean
    yield fixt_dict
    shutil.rmtree(os.path.dirname(local_vars["test_raw"]))


def test_dcm2niix(ref_info):
    # load ref, test data
    ref_t1w = ref_info["ref_t1w"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    test_t1w = ref_info["test_t1w"]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    assert (test_data == ref_data).all()
