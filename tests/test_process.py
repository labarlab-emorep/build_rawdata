import pytest
import json
import nibabel as nib


@pytest.mark.dcm_bids
def test_dcm2niix_build(fixt_dcm2nii):
    assert 4 == len(fixt_dcm2nii.raw_nii)
    assert 4 == len(fixt_dcm2nii.raw_json)


@pytest.mark.dcm_bids
def test_dcm2niix_anat(fixt_dcm2nii):
    img = nib.load(fixt_dcm2nii.raw_nii[0])
    assert (256, 256, 192) == img.shape

    with open(fixt_dcm2nii.raw_json[0]) as jf:
        anat_dict = json.load(jf)
    assert "EmoRep_anat" == anat_dict["ProtocolName"]
    assert 1 == anat_dict["SliceThickness"]
    assert 0.00312 == anat_dict["EchoTime"]
    assert 9 == anat_dict["FlipAngle"]


@pytest.mark.dcm_bids
def test_dcm2niix_func(fixt_dcm2nii):
    img = nib.load(fixt_dcm2nii.raw_nii[1])
    assert (128, 128, 69, 262) == img.shape

    with open(fixt_dcm2nii.raw_json[1]) as jf:
        func_dict = json.load(jf)
    assert "EmoRep_run01" == func_dict["ProtocolName"]
    assert 2 == func_dict["SliceThickness"]
    assert 0.03 == func_dict["EchoTime"]
    assert 90 == func_dict["FlipAngle"]


@pytest.mark.dcm_bids
def test_dcm2niix_fmap(fixt_dcm2nii):
    img = nib.load(fixt_dcm2nii.raw_nii[2])
    assert (128, 128, 69, 2) == img.shape

    with open(fixt_dcm2nii.raw_json[2]) as jf:
        fmap_dict = json.load(jf)
    assert "Field_Map_P>>A" == fmap_dict["ProtocolName"]
    assert 2 == fmap_dict["SliceThickness"]
    assert 0.03 == fmap_dict["EchoTime"]
    assert 90 == fmap_dict["FlipAngle"]


@pytest.mark.dcm_bids
def test_dcm2niix_rest(fixt_dcm2nii):
    img = nib.load(fixt_dcm2nii.raw_nii[3])
    assert (128, 128, 69, 240) == img.shape

    with open(fixt_dcm2nii.raw_json[3]) as jf:
        rest_dict = json.load(jf)
    assert "Rest_run01" == rest_dict["ProtocolName"]
    assert 2 == rest_dict["SliceThickness"]
    assert 0.03 == rest_dict["EchoTime"]
    assert 90 == rest_dict["FlipAngle"]


@pytest.mark.deface
def test_deface(fixt_deface):
    img_ref = nib.load(fixt_deface.ref_deface)
    data_ref = img_ref.get_fdata()
    img_tst = nib.load(fixt_deface.tst_deface)
    data_tst = img_tst.get_fdata()
    assert (data_ref == data_tst).all()
