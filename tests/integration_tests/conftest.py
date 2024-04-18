import pytest
import os
import sys
from typing import Iterator
import pandas as pd
from build_rawdata.resources import emorep
from build_rawdata import workflows

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import setup_data  # noqa: E402


class IntegTestVars:
    """Allow each fixture to add respective attrs."""

    pass


@pytest.fixture(scope="package")
def fixt_emorep_setup(fixt_setup) -> Iterator[IntegTestVars]:
    """Yield setup resources for emorep methods."""
    # Make testing sourcedata dirs
    map_src_dst = {}
    map_name_data = {
        "mri": "DICOM/20220429.ER0009.ER0009",
        "beh": "Scanner_behav",
        "phys": "Scanner_physio",
    }
    for name, dir_name in map_name_data.items():
        tst_dir = os.path.join(
            fixt_setup.test_dir,
            "sourcedata",
            fixt_setup.subjid,
            f"{fixt_setup.sessid}_{fixt_setup.taskid}",
            dir_name,
        )
        if not os.path.exists(tst_dir):
            os.makedirs(tst_dir)

        # Build source-dest mapping
        ref_dir = os.path.join(fixt_setup.subj_source, dir_name)
        map_src_dst[name] = [ref_dir, tst_dir]

    # Get testing sourcedata files
    task_path, rate_path = setup_data.get_behav(
        fixt_setup.subjid,
        fixt_setup.sessid,
        map_src_dst["beh"][0],
        map_src_dst["beh"][1],
    )
    setup_data.get_dicoms(
        fixt_setup.runid,
        os.path.dirname(map_src_dst["mri"][0]),
        map_src_dst["mri"][1],
    )
    phys_path = setup_data.get_phys(
        fixt_setup.subjid,
        fixt_setup.sessid,
        map_src_dst["phys"][0],
        map_src_dst["phys"][1],
    )

    # Test in new rawdata to avoid breaking unit tests
    raw_path = os.path.join(fixt_setup.test_dir, "rawdata_integ")
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)

    # Build and yield obj
    supp_setup = IntegTestVars()
    supp_setup.raw_path = raw_path
    supp_setup.task_path = task_path
    supp_setup.rate_path = rate_path
    supp_setup.phys_path = phys_path
    supp_setup.dcm_path = os.path.dirname(map_src_dst["mri"][1])

    yield supp_setup


@pytest.fixture(scope="module")
def fixt_emorep_mri(fixt_setup, fixt_emorep_setup) -> Iterator[IntegTestVars]:
    """Yield resources for testing emorep MRI wf."""
    # Run emorep MRI methods
    proc_mri = emorep.ProcessMri(fixt_setup.subjid, fixt_emorep_setup.raw_path)
    cont_pipe, anat_list = proc_mri.bids_nii(fixt_emorep_setup.dcm_path)
    deface_path = proc_mri.deface_anat(
        os.path.join(fixt_setup.test_dir, "derivatives")
    )

    # Build and yield obj
    supp_mri = IntegTestVars()
    supp_mri.cont_pipe = cont_pipe
    supp_mri.anat_list = anat_list
    supp_mri.deface_path = deface_path
    yield supp_mri


@pytest.fixture(scope="function")
def fixt_emorep_beh(fixt_setup, fixt_emorep_setup) -> Iterator[IntegTestVars]:
    """Yield resources for testing emorep behavior wf."""
    # Run emorep behavior methods
    proc_beh = emorep.ProcessBeh(fixt_setup.subjid, fixt_emorep_setup.raw_path)
    tsv_path, json_path = proc_beh.make_events(fixt_emorep_setup.task_path)

    # Build and yield obj
    supp_beh = IntegTestVars()
    supp_beh.tsv_path = tsv_path
    supp_beh.json_path = json_path
    yield supp_beh


@pytest.fixture(scope="function")
def fixt_emorep_rest(fixt_setup, fixt_emorep_setup) -> Iterator[IntegTestVars]:
    """Yield resources for testing emorep rest MRI wf."""
    # Run emorep rest behavior methods
    proc_rest = emorep.ProcessRate(
        fixt_setup.subjid, fixt_emorep_setup.raw_path
    )
    _, rest_path = proc_rest.make_rate(fixt_emorep_setup.rate_path)

    # Build and yield obj
    supp_rest = IntegTestVars()
    supp_rest.rest_path = rest_path
    yield supp_rest


@pytest.fixture(scope="module")
def fixt_emorep_phys(fixt_setup, fixt_emorep_setup) -> Iterator[IntegTestVars]:
    """Yield resources for testing emorep physio wf."""
    # Run emorep rest behavior methods
    proc_phys = emorep.ProcessPhys(
        fixt_setup.subjid, fixt_emorep_setup.raw_path
    )
    phys_path = proc_phys.make_physio(fixt_emorep_setup.phys_path)
    df = pd.read_csv(phys_path.replace(".acq", ".txt"), sep="\t", header=None)

    # Build and yield obj
    supp_phys = IntegTestVars()
    supp_phys.phys_path = phys_path
    supp_phys.df = df
    yield supp_phys


@pytest.fixture(scope="function")
def fixt_wf_emorep(fixt_setup, fixt_emorep_setup) -> Iterator[IntegTestVars]:
    """Yield resources for testing emorep wf."""
    # Run entire build_rawdata for EmoRep
    build_emo = workflows.BuildEmoRep(
        os.path.join(fixt_setup.test_dir, "sourcedata"),
        fixt_emorep_setup.raw_path,
        os.path.join(fixt_setup.test_dir, "derivatives"),
        True,
    )
    chk_pass = build_emo.chk_sourcedata(fixt_setup.subjid)
    build_emo.convert_mri()
    build_emo.convert_beh()
    build_emo.convert_phys()
    build_emo.convert_rate()

    # Make and yield obj
    supp_wf = IntegTestVars()
    supp_wf.chk_pass = chk_pass
    supp_wf.raw_path = fixt_emorep_setup.raw_path
    supp_wf.source_path = os.path.join(fixt_setup.test_dir, "sourcedata")
    supp_wf.deriv_path = os.path.join(fixt_setup.test_dir, "derivatives")
    yield supp_wf


@pytest.fixture(scope="module")
def fixt_wf_nki() -> Iterator[IntegTestVars]:
    """Yield resources for testing NKI wf."""
    setup_data.check_test_env()

    # Hardcode variables for known output
    age = 79
    dryrun = False
    hand = "L"
    nki_dir = (
        "/mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival"
        + "/code/nki_resources"
    )
    proj_dir = (
        "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
        + "/code/unit_test/build_rawdata"
    )
    prot = "REST645"
    scan = ["anat", "func"]
    sess = "BAS1"

    # Make yield obj, add attrs
    supp_nki = IntegTestVars()
    supp_nki.raw_dict = workflows.build_nki(
        age, dryrun, hand, nki_dir, proj_dir, prot, scan, sess
    )
    supp_nki.raw_path = os.path.join(proj_dir, "data_mri_BIDS", "rawdata")
    yield supp_nki
