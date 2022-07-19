"""Unit testing of dcm_conversion.convert.

Written for labaserv2, keoki environment.
"""
import pytest
import os
import nibabel as nib

try:
    from dcm_conversion import convert
except ImportError:
    dcm_conversion = None


def test_dcm2niix(ref_info):
    # Load ref data
    ref_t1w = ref_info["ref_t1w"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w = ref_info["test_t1w"]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()


def test_bidsify(ref_info):
    # Test naming
    ref_name = os.path.basename(ref_info["ref_t1w"])
    test_name = os.path.basename(ref_info["test_t1w"])
    assert ref_name == test_name
