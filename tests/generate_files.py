import os
import subprocess


def setup():
    """Setup for build_rawdata unit testing.

    Assumes build_rawdata has already (successfully)
    converted data for ER0009.
    """
    test_par = (
        "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
        + "/code/unit_test/build_rawdata"
    )
    print(f"Setting up directory for testing:\n\t{test_par}\n")

    # Set orienting vars
    subid = "ER0009"
    sess = "ses-day2"
    task = "task-movies"
    run = "run-01"
    proj_dir = (
        "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS"
    )

    # Setup unit test dir
    test_raw = os.path.join(test_par, "rawdata", f"sub-{subid}", sess)
    test_raw_anat = os.path.join(test_raw, "anat")
    test_raw_func = os.path.join(test_raw, "func")
    test_deface = os.path.join(
        test_par, "derivatives/deface", f"sub-{subid}", sess
    )
    for h_dir in [test_raw_anat, test_raw_func, test_deface]:
        if not os.path.exists(h_dir):
            os.makedirs(h_dir)

    # Set paths to project data
    proj_raw = os.path.join(proj_dir, "rawdata", f"sub-{subid}", sess)
    proj_deface = os.path.join(
        proj_dir, "derivatives/deface", f"sub-{subid}", sess
    )

    # Copy anat
    print("\tCopying rawdata files ...")
    cp_anat = f"rsync -au {proj_raw}/anat/*.nii.gz {test_raw_anat}"
    cp_sp = subprocess.Popen(cp_anat, shell=True, stdout=subprocess.PIPE)
    _ = cp_sp.communicate()

    # Copy func
    cp_func = f"rsync -au {proj_raw}/func/*{task}_{run}* {test_raw_func}"
    cp_sp = subprocess.Popen(cp_func, shell=True, stdout=subprocess.PIPE)
    _ = cp_sp.communicate()

    # Copy deface
    print("\tCopying deface file ...")
    cp_deface = f"rsync -au {proj_deface}/*.nii.gz {test_deface}"
    cp_sp = subprocess.Popen(cp_deface, shell=True, stdout=subprocess.PIPE)
    _ = cp_sp.communicate()


if __name__ == "__main__":
    setup()
