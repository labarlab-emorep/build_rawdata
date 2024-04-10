import pytest
import os
import shutil


class SupplyVars:
    pass


@pytest.fixture(scope="session")
def fixt_setup():
    # Start object for yielding
    obj_setup = SupplyVars()

    # Hardcode variables for specific testing
    obj_setup.subid = "ER0009"
    obj_setup.subj = "sub-" + obj_setup.subid
    obj_setup.sess = "ses-day2"
    obj_setup.task = "task-movies"
    obj_setup.run = "run-01"
    par_dir = "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
    obj_setup.proj_dir = os.path.join(par_dir, "data_scanner_BIDS")

    # Make testing output parent directories
    obj_setup.test_dir = os.path.join(par_dir, "code/unit_test/build_rawdata")
    for _dir in ["rawdata", "derivatives"]:
        mk_dir = os.path.join(obj_setup.test_dir, _dir)
        if not os.path.exists(mk_dir):
            os.makedirs(mk_dir)

    # Yield and teardown
    yield obj_setup
    return  # TODO remove
    shutil.rmtree(obj_setup.test_dir)
