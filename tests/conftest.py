import pytest
import os
import glob
import shutil
import subprocess
import pandas as pd
from build_rawdata.resources import behavior
from build_rawdata.resources import bidsify
from build_rawdata.resources import process
import generate_files


@pytest.fixture(scope="session")
def fixt_setup():
    # Hardcode variables for specific testing
    subid = "ER0009"
    sess = "ses-day2"
    task = "task-movies"
    run = "run-01"
    proj_dir = (
        "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS"
    )
    test_par = (
        "/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion"
        + "/code/unit_test/build_rawdata"
    )

    # Setup reference variables
    subj = "sub-" + subid
    ref_raw = os.path.join(test_par, "rawdata")
    ref_deriv = os.path.join(test_par, "derivatives")
    ref_t1w = os.path.join(
        ref_raw, subj, sess, "anat/sub-ER0009_ses-day2_T1w.nii.gz"
    )
    ref_raw_subj_sess = os.path.join(ref_raw, subj, sess)
    ref_deface = os.path.join(
        ref_deriv,
        "deface",
        subj,
        sess,
        f"{subj}_{sess}_T1w_defaced.nii.gz",
    )
    ref_beh_tsv = os.path.join(
        ref_raw_subj_sess,
        f"func/{subj}_{sess}_{task}_{run}_events.tsv",
    )
    ref_beh_json = os.path.join(
        ref_raw_subj_sess,
        f"func/{subj}_{sess}_{task}_{run}_events.json",
    )

    # Check for setup
    missing_raw = False if os.path.exists(ref_t1w) else True
    missing_deface = False if os.path.exists(ref_deface) else True
    if missing_raw or missing_deface:
        generate_files.setup(subid, sess, task, run, proj_dir, test_par)

    # Setup test variables
    test_dir = os.path.join(test_par, "test_out")
    test_subj = os.path.join(test_dir, subj)
    test_subj_sess = os.path.join(test_subj, sess)

    yield {
        "subid": subid,
        "subj": subj,
        "sess": sess,
        "task": task,
        "proj_dir": proj_dir,
        "ref_raw_subj_sess": ref_raw_subj_sess,
        "ref_t1w": ref_t1w,
        "ref_deface": ref_deface,
        "ref_beh_tsv": ref_beh_tsv,
        "ref_beh_json": ref_beh_json,
        "test_dir": test_dir,
        "test_subj": test_subj,
        "test_subj_sess": test_subj_sess,
    }

    # TODO remove return once tests are working
    return
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture(scope="package")
def fixt_dcm_bids(fixt_setup):
    # Make output dir
    out_dir = fixt_setup["test_subj_sess"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Find dicom dir
    source_subj = os.path.join(
        fixt_setup["proj_dir"], "sourcedata", fixt_setup["subid"]
    )
    dcm_dir = sorted(glob.glob(f"{source_subj}/day*/DICOM"))[0]

    # Conduct dcm2niix, bidsify
    nii_list, json_list = process.dcm2niix(
        dcm_dir,
        out_dir,
        fixt_setup["subid"],
        fixt_setup["sess"],
    )

    bn = bidsify.BidsifyNii(
        out_dir, fixt_setup["subj"], fixt_setup["sess"], fixt_setup["task"]
    )
    t1_list = bn.bids_nii()
    bn.update_func()
    bn.update_fmap()

    # Yield dict and teardown
    yield {
        "nii_list": nii_list,
        "json_list": json_list,
        "test_t1w": t1_list[0],
    }

    # TODO remove return once tests are working
    return
    shutil.rmtree(out_dir)


@pytest.fixture(scope="function")
def fixt_deface(fixt_setup):
    # Execute deface method
    deface_list = process.deface(
        [fixt_setup["ref_t1w"]],
        fixt_setup["test_dir"],
        fixt_setup["subid"],
        fixt_setup["sess"],
    )

    # Yield and teardown
    yield {"test_deface": deface_list[0]}

    # TODO remove return once tests are working
    return
    shutil.rmtree(os.path.join(fixt_setup["test_dir"], "deface"))


@pytest.fixture(scope="function")
def fixt_exp_bids(fixt_setup):
    # Setup output location
    out_dir = fixt_setup["test_subj"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Run method
    data_desc, read_me, ignore_file = bidsify.bidsify_exp(out_dir)

    # Yield and teardown
    yield {
        "data_desc": data_desc,
        "read_me": read_me,
        "ignore_file": ignore_file,
    }

    # TODO remove return once tests are working
    return
    for h_file in [data_desc, read_me, ignore_file]:
        if os.path.exists(h_file):
            os.remove(h_file)


@pytest.fixture(scope="module")
def fixt_behavior(fixt_setup):
    # Make out_dir
    out_dir = fixt_setup["test_subj"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Find source csv
    source_subj = os.path.join(
        fixt_setup["proj_dir"], "sourcedata", fixt_setup["subid"]
    )
    task_file = sorted(
        glob.glob(f"{source_subj}/day*/Scanner_behav/*run-1*csv")
    )[0]

    # Execute behavior.events method
    events_tsv, events_json = behavior.events_tsv(
        task_file,
        out_dir,
        fixt_setup["subid"],
        fixt_setup["sess"],
        fixt_setup["task"],
        "run-01",
    )

    # Yield and teardown
    yield {
        "events_tsv": events_tsv,
        "events_json": events_json,
    }

    # TODO remove return once tests are working
    return
    for h_file in [events_json, events_tsv]:
        if os.path.exists(h_file):
            os.remove(h_file)


@pytest.fixture(scope="function")
def fixt_rest_ratings(fixt_setup):
    # Make rest rating output from sourcedata
    rate_path = os.path.join(
        fixt_setup["proj_dir"],
        "sourcedata",
        fixt_setup["subid"],
        "day3_scenarios",
        "Scanner_behav/emorep_RestRatingData_sub-ER0009_ses-day3_04282022.csv",
    )
    subj_raw = os.path.join(fixt_setup["test_subj_sess"], "beh")
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    out_file = os.path.join(
        subj_raw,
        f"sub-{fixt_setup['subid']}_{fixt_setup['sess']}_rest-ratings.tsv",
    )
    df_rest = behavior.rest_ratings(
        rate_path, fixt_setup["subid"], fixt_setup["sess"], out_file
    )
    df_rest["resp_int"] = df_rest["resp_int"].astype("int64")

    # Copy existing rawdata rest ratings to reference location
    ref_beh = os.path.join(fixt_setup["ref_raw_subj_sess"], "beh")
    if not os.path.exists(ref_beh):
        os.makedirs(ref_beh)
    real_file = f"{fixt_setup['subj']}_ses-day3_rest-ratings_2022-04-28.tsv"
    rest_path = os.path.join(
        fixt_setup["proj_dir"],
        "rawdata",
        fixt_setup["subj"],
        "ses-day3/beh",
        real_file,
    )
    cp_sp = subprocess.Popen(
        f"rsync -rau {rest_path} {ref_beh}", shell=True, stdout=subprocess.PIPE
    )
    _ = cp_sp.communicate()
    ref_path = os.path.join(ref_beh, real_file)
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Missing reference file : {ref_path}")
    df_ref = pd.read_csv(ref_path, sep="\t")

    yield {
        "df_rest": df_rest,
        "df_ref": df_ref,
    }

    # TODO teardown
