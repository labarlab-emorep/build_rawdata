"""Title.

Desc.
"""
import os
import sys
import glob
import shutil
import subprocess
import textwrap
import json


def _error_msg(msg, stdout, stderr):
    """Title.

    Desc.
    """
    error_message = f"""\
            {msg}

            stdout
            ------
            {stdout}

            stderr
            ------
            {stderr}
        """
    print(textwrap.dedent(error_message))


def _switch_name(old_name, subj, sess, task="", run: str = ""):
    """Title.

    Desc.
    """
    base_str = f"sub-{subj}_{sess}"
    name_dict = {
        "DICOM_EmoRep_anat": ("anat", f"{base_str}_T1w"),
        f"DICOM_EmoRep_run{run}": (
            "func",
            f"{base_str}_task-{task}_run-{run}_bold",
        ),
        f"DICOM_Rest_run{run}": (
            "func",
            f"{base_str}_task-rest_run-{run}_bold",
        ),
        "DICOM_Field_Map_P_A": ("fmap", f"{base_str}_acq-rpe_dir-PA_epi"),
    }
    return name_dict[old_name]


def dcm2niix(subj_source, subj_raw, subj, sess, task):
    """Title.

    Desc.
    """
    # setup output dir, construct and run dcm2niix
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)
    bash_cmd = f"""\
        dcm2niix \
            -a y \
            -ba y \
            -z y \
            -o {subj_raw} \
            {subj_source}
    """
    h_sp = subprocess.Popen(bash_cmd, shell=True, stdout=subprocess.PIPE)
    job_out, job_err = h_sp.communicate()
    h_sp.wait()

    # clean localizers, make nii/json lists, check
    for rm_file in glob.glob(f"{subj_raw}/DICOM_localizer*"):
        os.remove(rm_file)
    nii_list = glob.glob(f"{subj_raw}/*.nii.gz")
    json_list = glob.glob(f"{subj_raw}/*.json")
    if not nii_list or len(nii_list) != len(json_list):
        _error_msg("dcm2niix failed!", job_out, job_err)
        sys.exit(1)

    # move and rename nii files
    for h_nii, h_json in zip(nii_list, json_list):
        old_name = os.path.basename(h_nii).split("_20")[0]
        if "run" in old_name:
            run = old_name.split("run")[1]
            new_dir, new_name = _switch_name(old_name, subj, sess, task, run)
        else:
            new_dir, new_name = _switch_name(old_name, subj, sess)
        new_path = os.path.join(os.path.dirname(h_nii), new_dir)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        shutil.move(h_nii, f"{new_path}/{new_name}.nii.gz")
        shutil.move(h_json, f"{new_path}/{new_name}.json")

    # update fmap json with IntendedFor
    bold_list = [
        x.split(f"sub-{subj}/")[1]
        for x in sorted(glob.glob(f"{subj_raw}/func/*bold.nii.gz"))
    ]
    fmap_json = glob.glob(f"{subj_raw}/fmap/*json")[0]
    with open(fmap_json) as jf:
        fmap_dict = json.load(jf)
    fmap_dict["IntendedFor"] = bold_list
    with open(fmap_json, "w") as jf:
        json.dump(fmap_dict, jf)
