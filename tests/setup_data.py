"""Methods for finding, organizing data needed for testing.

par_dir : Provide path to project directory
test_dir : Provide path to unit test directory
check_test_env : Check for testing environment
get_behav : Copy run-01 behavior/rest files for testing
get_dicoms : Copy select DICOMs to testing location
get_phys : Copy select physiologic files to testing location

"""

import os
import shutil
import glob
import platform
from typing import Union


def par_dir() -> Union[str, os.PathLike]:
    """Return path to project directory."""
    return "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"


def test_dir() -> Union[str, os.PathLike]:
    """Return path to project testing directory."""
    return os.path.join(par_dir(), "code/unit_test/build_rawdata")


def check_test_env():
    """Raise EnvironmentError for improper testing envs."""
    # Check for labarserv2
    if "ccn-labarserv2" not in platform.uname().node:
        raise EnvironmentError("Please execute pytest on labarserv2")

    # Check for Nature env
    msg_nat = "Please execute pytest in emorep conda env"
    try:
        conda_env = os.environ["CONDA_DEFAULT_ENV"]
        if "emorep" not in conda_env:
            raise EnvironmentError(msg_nat)
    except KeyError:
        raise EnvironmentError(msg_nat)


def get_dicoms(
    runid: str, src: Union[str, os.PathLike], dst: Union[str, os.PathLike]
):
    """Copy select sourcedata DICOMs to test location."""
    # Check for source, output
    if not os.path.basename(src) == "DICOM":
        raise ValueError("Expected 'src' parameter : path to 'DICOM' dir")
    if glob.glob(f"{dst}/*dcm"):
        return

    # Copy DICOMs from specific directories to reduce dcm2niix execution time
    for cp_dir in [
        "EmoRep_anat",
        f"EmoRep_run{runid}",
        "Rest_run01",
        "Field_Map_PA",
    ]:
        # Check for existing BIDS organization
        chk_bids = os.path.join(os.path.dirname(dst), cp_dir)
        if os.path.exists(chk_bids):
            continue

        # Copy data with flat output organization
        shutil.copytree(os.path.join(src, cp_dir), dst, dirs_exist_ok=True)


def get_behav(
    subjid: str,
    sessid: str,
    src: Union[str, os.PathLike],
    dst: Union[str, os.PathLike],
) -> list:
    """Copy rest, task run-01 sourcedata behavior files to test location."""
    if not os.path.basename(src) == "Scanner_behav":
        raise ValueError(
            "Expected 'src' parameter : path to 'Scanner_behav' dir"
        )

    task_path = os.path.join(
        src,
        f"emorep_scannertextData_{subjid}_ses{sessid}_run1_04282022.csv",
    )
    rate_path = os.path.join(
        src,
        f"emorep_RestRatingData_sub-{subjid}_ses-{sessid}_04282022.csv",
    )
    out_list = []
    for cp_file in [task_path, rate_path]:
        out_path = os.path.join(dst, os.path.basename(cp_file))
        if os.path.exists(out_path):
            out_list.append(out_path)
            continue
        shutil.copy2(cp_file, dst)
        out_list.append(out_path)
    return out_list


def get_phys(
    subjid: str,
    sessid: str,
    src: Union[str, os.PathLike],
    dst: Union[str, os.PathLike],
) -> Union[str, os.PathLike]:
    """Copy run1 physio sourcedata behavior files to test location."""
    if not os.path.basename(src) == "Scanner_physio":
        raise ValueError(
            "Expected 'src' parameter : path to 'Scanner_physio' dir"
        )

    task_path = os.path.join(
        src,
        f"{subjid}_{sessid}_physio_run1.acq",
    )
    shutil.copy2(task_path, dst)
    return os.path.join(dst, os.path.basename(task_path))
