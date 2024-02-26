import os
import pytest
import nibabel as nib


@pytest.mark.dcm_bids
def test_dcm2niix(fixt_setup, fixt_dcm_niix):
    # Load ref data
    ref_t1w = fixt_setup["ref_t1w"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w_list = fixt_dcm_niix["anat_nii_list"]
    test_t1w = test_t1w_list[0]
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Make sure dcm2niix filename
    assert (
        os.path.basename(test_t1w)
        == "DICOM_EmoRep_anat_20220422131941_2.nii.gz"
    )

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()


@pytest.mark.deface
def test_deface(fixt_setup, fixt_deface):
    # Load ref data
    ref_t1w = fixt_setup["ref_deface"]
    ref_img = nib.load(ref_t1w)
    ref_data = ref_img.get_fdata()

    # Load test data
    test_t1w = fixt_deface["test_deface"]
    assert os.path.exists(test_t1w)
    test_img = nib.load(test_t1w)
    test_data = test_img.get_fdata()

    # Test that nii matrices are the same
    assert (test_data == ref_data).all()
