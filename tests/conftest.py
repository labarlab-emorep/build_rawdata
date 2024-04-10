import pytest
import os
import shutil
from build_rawdata.resources import behavior


class SupplyVars:
    pass


@pytest.fixture(scope="session")
def fixt_setup():
    """Yield setup resources."""
    # Start object for yielding
    obj_setup = SupplyVars()

    # Hardcode variables for specific testing
    obj_setup.subjid = "ER0009"
    obj_setup.sessid = "day3"
    obj_setup.taskid = "scenarios"
    obj_setup.subj = "sub-" + obj_setup.subjid
    obj_setup.sess = "ses-" + obj_setup.sessid
    obj_setup.task = "task-" + obj_setup.taskid
    obj_setup.run = "run-01"
    par_dir = "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
    obj_setup.proj_dir = os.path.join(par_dir, "data_scanner_BIDS")
    obj_setup.subj_source = os.path.join(
        obj_setup.proj_dir,
        "sourcedata",
        obj_setup.subjid,
        f"{obj_setup.sessid}_{obj_setup.taskid}",
    )

    # Make testing output parent directories
    obj_setup.test_dir = os.path.join(par_dir, "code/unit_test/build_rawdata")
    for _dir in ["rawdata", "derivatives"]:
        mk_dir = os.path.join(obj_setup.test_dir, _dir)
        if not os.path.exists(mk_dir):
            os.makedirs(mk_dir)

    # Yield and teardown
    yield obj_setup
    # return  # TODO remove
    shutil.rmtree(obj_setup.test_dir)


@pytest.fixture(scope="session")
def fixt_behavior(fixt_setup):
    """Yield resources for testing behavior module."""
    obj_beh = SupplyVars()
    task_path = os.path.join(
        fixt_setup.subj_source,
        "Scanner_behav",
        f"emorep_scannertextData_{fixt_setup.subjid}_"
        + f"ses{fixt_setup.sessid}_run1_04282022.csv",
    )

    #
    obj_beh.ev_info = behavior._EventsData(task_path)

    #
    subj_raw = os.path.join(
        fixt_setup.test_dir,
        "rawdata",
        fixt_setup.subj,
        fixt_setup.sess,
        "func",
    )
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    obj_beh.event_tsv, obj_beh.event_json = behavior.events_tsv(
        task_path,
        subj_raw,
        fixt_setup.subjid,
        fixt_setup.sess,
        fixt_setup.task,
        fixt_setup.run,
    )

    #
    rate_path = os.path.join(
        fixt_setup.subj_source,
        "Scanner_behav",
        f"emorep_RestRatingData_{fixt_setup.subj}_"
        + f"{fixt_setup.sess}_04282022.csv",
    )
    out_file = os.path.join(subj_raw, "tst_rest_ratings.tsv")
    obj_beh.df_rest = behavior.rest_ratings(
        rate_path, fixt_setup.subjid, fixt_setup.sess, out_file
    )

    yield obj_beh
