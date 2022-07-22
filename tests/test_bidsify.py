"""Unit testing of dcm_conversion.bidsify.

Written for labaserv2, keoki environment.
"""
import pytest
import os


def test_bidsify_nii(ref_info):
    # Test naming
    ref_name = os.path.basename(ref_info["ref_t1w"])
    test_name = os.path.basename(ref_info["test_t1w"])
    assert ref_name == test_name
