"""Unit testing of dcm_conversion.process.

Written for labaserv2, keoki environment.
"""
import pytest
import nibabel as nib


@pytest.mark.dcm2niix
def test_dcm2niix(info_dcm_bids):
    # Load ref data
    ref_t1w = info_dcm_bids["ref_t1w"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w = info_dcm_bids["test_t1w"]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()


@pytest.mark.deface
def test_deface(info_deface):
    # Load ref data
    ref_t1w = info_deface["ref_deface"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w = info_deface["test_deface"]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()
