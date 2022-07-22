"""Convert DICOMs to NIfTI files.

Use Chris Rorden's dcm2niix to convert DICOMs to NIfTI files. Also rename
files and restructure directory organizaton for BIDS compliance.

Notes
-----
Assumes flat DICOM organization.
BIDS file naming is EmoRep specific (_switch_name).
Assumes T1w exist for each session.
"""
import os
import glob
import shutil
import subprocess
import textwrap
import json


def _error_msg(msg, stdout, stderr):
    """Print stdout and stderr."""
    error_message = f"""
            {msg}

            stdout
            ------
            {stdout}

            stderr
            ------
            {stderr}
        """
    print(textwrap.dedent(error_message))


def _switch_name(old_name, subid, sess, task="", run: str = ""):
    """Determine EmoRep file types.

    Use default filename string output by dcm2niix to
    determine the type and name of NIfTI file.

    Parameters
    ----------
    old_name : str
        Split dcm2niix name, preceding year date
        e.g. DICOM_EmoRep_anat for DICOM_EmoRep_anat_20220101_foo.nii.gz
    subid : str
        Subject identifier, BIDS label
    sess : str
        BIDS-formatted session string
    task : str, optional
        BIDS-formatted task string
    run : str, optional
        Run number, BIDS label

    Returns
    -------
    tuple
        [0] = scan type (anat, func, fmap)
        [1] = BIDS-formatted file name, sans extension
    """
    base_str = f"sub-{subid}_{sess}"
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


def dcm2niix(subj_source, subj_raw, subid, sess, task):
    """Conduct dcm2niix.

    Point dcm2niix at a DICOM directory, rename NIfTI
    files according to BIDs specifications, and update
    fmap json files with "IntendedFor" field.

    Parameters
    ----------
    subj_source : Path
        Subject's DICOM directory in sourcedata
    subj_raw : Path
        Subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string
    task : str
        BIDS-formatted task string

    Notes
    -----
    Writes dcm2niix-named NIfTI files to subject's rawdata.

    Returns
    -------
    tuple
        [0] = list of output niis
        [1] = list of output jsons

    Raises
    ------
    FileNotFoundError
        If NIFTI files are not dected in subject rawdata.
        If the number of NIfTI and JSON are != in subject rawdata.
    """
    # Construct and run dcm2niix cmd
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

    # Clean localizers, make nii/json lists
    for rm_file in glob.glob(f"{subj_raw}/DICOM_localizer*"):
        os.remove(rm_file)
    nii_list = glob.glob(f"{subj_raw}/*.nii.gz")
    json_list = glob.glob(f"{subj_raw}/*.json")

    # Check that dcm2nix worked
    if job_out:
        job_out = job_out.decode("utf-8")
    if job_err:
        job_err = job_err.decode("utf-8")
    if not nii_list:
        _error_msg("dcm2niix failed!", job_out, job_err)
        raise FileNotFoundError("No nii files detected.")
    elif len(nii_list) != len(json_list):
        raise FileNotFoundError("Unbalanced json and nii lists.")

    return (nii_list, json_list)


def bidsify_nii(nii_list, json_list, subj_raw, subid, sess, task):
    """Move data into BIDS organization.

    Rename/reorganize NIfTI files according to BIDs specifications,
    and update fmap json files with "IntendedFor" field.

    Parameters
    ----------
    nii_list : list
        Paths to nii files output by dcm2niix
    json_list : list
        Paths to json files output by dcm2niix
    subj_raw : Path
        Subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string
    task : str
        BIDS-formatted task string

    Returns
    -------
    t1_list : list
        Path and name of session T1w files

    Raises
    ------
    FileNotFoundError
        If BIDS-organized T1w files are not found for the session.
    """
    # Move and rename nii files
    print(f"\t Renaming, organizing NIfTIs for sub-{subid}, {sess} ...")
    for h_nii, h_json in zip(nii_list, json_list):
        old_name = os.path.basename(h_nii).split("_20")[0]
        if "run" in old_name:
            run = old_name.split("run")[1]
            new_dir, new_name = _switch_name(old_name, subid, sess, task, run)
        else:
            new_dir, new_name = _switch_name(old_name, subid, sess)
        new_path = os.path.join(os.path.dirname(h_nii), new_dir)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        shutil.move(h_nii, f"{new_path}/{new_name}.nii.gz")
        shutil.move(h_json, f"{new_path}/{new_name}.json")

    # Make T1w list for return
    t1_list = sorted(glob.glob(f"{subj_raw}/anat/*T1w.nii.gz"))
    if not t1_list:
        raise FileNotFoundError("No BIDS-organized T1w files detected.")

    # Update fmap json with "IntendedFor" field
    print(f"\t Updating fmap jsons for sub-{subid}, {sess} ...")
    bold_list = [
        x.split(f"sub-{subid}/")[1]
        for x in sorted(glob.glob(f"{subj_raw}/func/*bold.nii.gz"))
    ]
    fmap_json = glob.glob(f"{subj_raw}/fmap/*json")[0]
    with open(fmap_json) as jf:
        fmap_dict = json.load(jf)
    fmap_dict["IntendedFor"] = bold_list
    with open(fmap_json, "w") as jf:
        json.dump(fmap_dict, jf)

    # Update func jsons with "TaskName" Field, account for task/rest
    print(f"\t Updating func jsons for sub-{subid}, {sess} ...")
    func_json_all = sorted(glob.glob(f"{subj_raw}/func/*_bold.json"))
    for func_json in func_json_all:
        h_task = func_json.split("_task-")[1].split("_")[0]
        with open(func_json) as jf:
            func_dict = json.load(jf)
        func_dict["TaskName"] = h_task
        with open(func_json, "w") as jf:
            json.dump(func_dict, jf)

    return t1_list


def bidsify_exp(raw_path):
    """Title.

    Desc.
    """
    # Generate dataset_description file
    data_desc = {
        "Name": "EmoRep",
        "BIDSVersion": "1.7.0",
        "DatasetType": "raw",
        "Funding": ["1R01MH113238"],
        "GeneratedBy": [{"Name": "dcm2niix", "Version": "v1.0.20211006"}],
    }
    with open(f"{raw_path}/dataset_description.json", "w") as jf:
        json.dump(data_desc, jf)

    # Generate README file
    with open(f"{raw_path}/README", "w") as rf:
        rf.write("TODO: update")
