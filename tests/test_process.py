"""Unit testing of dcm_conversion.process.

Written for labaserv2, keoki environment.
"""
import pytest
import os
import nibabel as nib

try:
    from dcm_conversion import process
except ImportError:
    dcm_conversion = None


def test_deface(ref_info):
    # Load ref data
    ref_t1w = ref_info["ref_deface"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w = ref_info["test_deface"]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()
