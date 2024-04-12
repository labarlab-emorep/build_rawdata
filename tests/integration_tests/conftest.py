import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import setup_data  # noqa: E402


class IntegTestVars:
    pass


@pytest.fixture(scope="session")
def fixt_emorep(fixt_setup):
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
        ref_dir = os.path.join(fixt_setup.subj_source, dir_name)
        map_src_dst[name] = [ref_dir, tst_dir]
        if not os.path.exists(tst_dir):
            os.makedirs(tst_dir)

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
