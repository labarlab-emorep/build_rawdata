"""Methods for making data BIDS compliant.

Notes
-----
BIDS file naming is EmoRep specific (_switch_name).

"""
import os
import glob
import shutil
import json
from dcm_conversion.resources import unique_cases


def _switch_name(dcm2niix_name, subid, sess, task="", run: str = ""):
    """Determine EmoRep file types.

    Use default filename string output by dcm2niix to
    determine the type and name of NIfTI file.

    Parameters
    ----------
    dcm2niix_name : str
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
    # Start BIDS file name string
    base_str = f"sub-{subid}_{sess}"

    # Key is from dcm2niix file names, value tuple contains
    # BIDS directory and file names.
    name_dict = {
        "DICOM_EmoRep_anat": ("anat", f"{base_str}_T1w"),
        f"DICOM_EmoRep_run{run}": (
            "func",
            f"{base_str}_{task}_run-{run}_bold",
        ),
        f"DICOM_Rest_run{run}": (
            "func",
            f"{base_str}_task-rest_run-{run}_bold",
        ),
        "DICOM_Field_Map_P_A": ("fmap", f"{base_str}_acq-rpe_dir-PA_epi"),
        f"DICOM_Field_Map_P_A_run{run}": (
            "fmap",
            f"{base_str}_acq-rpe_dir-PA_run-{run}_epi",
        ),
    }
    return name_dict[dcm2niix_name]


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
    subj_raw : path
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
    print(f"\t Renaming, organizing NIfTIs for sub-{subid}, {sess} ...")

    # Rename and move each file in nii, json lists
    nii_json_list = nii_list + json_list
    for h_file in nii_json_list:

        # Get first part of file name, use as key in dict-switch to
        # get (new) BIDS directory and file name.
        dcm2niix_name = os.path.basename(h_file).split("_20")[0]
        if "run" in dcm2niix_name:
            run = dcm2niix_name.split("run")[1]
            bids_dir, bids_name = _switch_name(
                dcm2niix_name, subid, sess, task, run
            )
        else:
            bids_dir, bids_name = _switch_name(dcm2niix_name, subid, sess)

        # Setup path to new BIDs directory
        bids_path = os.path.join(os.path.dirname(h_file), bids_dir)
        if not os.path.exists(bids_path):
            os.makedirs(bids_path)

        # Determine extension, move and rename json, nii files
        file_ext = (
            ".json" if os.path.splitext(h_file)[1] == ".json" else ".nii.gz"
        )
        shutil.move(h_file, f"{bids_path}/{bids_name}{file_ext}")

    # Make T1w list for return
    t1_list = sorted(glob.glob(f"{subj_raw}/anat/*T1w.nii.gz"))
    if not t1_list:
        raise FileNotFoundError("No BIDS-organized T1w files detected.")

    # Update fmap json with "IntendedFor" field
    print(f"\t Updating fmap jsons for sub-{subid}, {sess} ...")
    try:
        # Extract session and file name, per BIDS validator reqs
        bold_list = [
            x.split(f"sub-{subid}/")[1]
            for x in sorted(glob.glob(f"{subj_raw}/func/*bold.nii.gz"))
        ]

        # Get list of fmap json files
        fmap_json_list = sorted(glob.glob(f"{subj_raw}/fmap/*json"))
        fmap_count = len(fmap_json_list)

        # Update fmap jsons with intended lists
        if fmap_count == 1:
            fmap_json = fmap_json_list[0]
            # Open fmap json
            with open(fmap_json) as jf:
                fmap_dict = json.load(jf)

            # Update fmap json with intended list, write
            fmap_dict["IntendedFor"] = bold_list
            with open(fmap_json, "w") as jf:
                json.dump(fmap_dict, jf)

        elif fmap_count == 2:
            # Check to see if this session needs to
            # be handled as a unique case. If not,
            # divide the func runs between the fmaps
            bold_lists = unique_cases.fmap_issue(sess, subid, bold_list)
            if bold_lists is None:
                bold_count = len(bold_list)
                bold_per_fmap = round(bold_count / fmap_count)
                bold_lists = []
                bold_lists.append(bold_list[:bold_per_fmap])
                bold_lists.append(bold_list[bold_per_fmap:])
            # TODO: use zip instead of pop
            for fmap_json in fmap_json_list:
                # Open fmap json
                with open(fmap_json) as jf:
                    fmap_dict = json.load(jf)

                # Update fmap json with intended list, write
                fmap_dict["IntendedFor"] = bold_lists.pop(0)
                with open(fmap_json, "w") as jf:
                    json.dump(fmap_dict, jf)

        elif fmap_count > 2:
            raise RuntimeError("More than 2 fmap images found!")

    except IndexError:
        print(f"\t\t No fmaps detected for sub-{subid}, skipping.")

    # Update func jsons with "TaskName" Field, account for task/rest
    print(f"\t Updating func jsons for sub-{subid}, {sess} ...")
    func_json_all = sorted(glob.glob(f"{subj_raw}/func/*_bold.json"))
    for func_json in func_json_all:

        # Get task name, open json
        h_task = func_json.split("_task-")[1].split("_")[0]
        with open(func_json) as jf:
            func_dict = json.load(jf)

        # Update, write json
        func_dict["TaskName"] = h_task
        with open(func_json, "w") as jf:
            json.dump(func_dict, jf)

    return t1_list


def bidsify_exp(raw_path):
    """Create experiment-level BIDS files.

    Write dataset_description.json, README, and .bidsignore.

    Parameters
    ----------
    raw_path : path
        Location of parent rawdata directory

    Returns
    -------
    list
        Paths to written files

    """
    # Generate dataset_description file
    file_desc = f"{raw_path}/dataset_description.json"
    data_desc = {
        "Name": "EmoRep",
        "BIDSVersion": "1.7.0",
        "DatasetType": "raw",
        "Funding": ["1R01MH113238"],
        "GeneratedBy": [{"Name": "dcm2niix", "Version": "v1.0.20211006"}],
    }
    with open(file_desc, "w") as jf:
        json.dump(data_desc, jf)

    # Generate README file
    file_readme = f"{raw_path}/README"
    with open(file_readme, "w") as rf:
        rf.write("TODO: update")

    # Add ignore file for physio data
    file_ignore = f"{raw_path}/.bidsignore"
    with open(file_ignore, "w") as igf:
        igf.write("**/*.acq")

    return [file_desc, file_readme, file_ignore]
