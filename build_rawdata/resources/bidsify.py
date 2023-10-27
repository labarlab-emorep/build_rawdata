"""Methods for making data BIDS compliant."""
import os
import glob
import shutil
import json
from typing import Union
from build_rawdata.resources import unique_cases


class BidsifyNii:
    """Move dcm2niix output in rawdata into BIDS organiztion.

    Methods
    -------
    bids_nii()
        BIDS-organize rawdata NIfTIs
    update_func()
        Update func json with TaskName
    update_fmap()
        Update fmap json with IntendedFor

    Example
    -------
    bn = BidsifyNii(
        "/path/to/rawdata/sub-1234/ses-day1",
        "sub-1234",
        "ses-day1",
        "task-foo",
    )
    bn.bids_nii()
    bn.update_func()
    bn.update_fmap()

    """

    def __init__(self, subj_raw, subj, sess, task):
        """Initialize."""
        print("\t\t\tInitializing BidsifyNii")
        self._subj_raw = subj_raw
        self._subj = subj
        self._sess = sess
        self._task = task

    def bids_nii(self):
        """BIDS-organize NIfTI and JSON files.

        Returns
        -------
        list
            paths to nii anat files

        """
        # Find files for organizing
        nii_list = sorted(glob.glob(f"{self._subj_raw}/*.nii.gz"))
        json_list = sorted(glob.glob(f"{self._subj_raw}/*.json"))
        if not nii_list:
            raise FileNotFoundError(
                f"Expected raw dcm2niix output in {self._subj_raw}"
            )
        nii_json_list = nii_list + json_list

        # Rename, organize each nii/json file
        print(
            "\t\t\t\tRenaming, organizing NIfTIs for "
            + f"{self._subj}, {self._sess} ..."
        )
        for h_file in nii_json_list:
            # Get first part of file name, use as key in dict-switch to
            # get (new) BIDS directory and file name. Manage new fmap
            # protocol names being called P_A_run1 and P_A_run_2.
            dcm2niix_name = os.path.basename(h_file).split("_20")[0]
            if "run" in dcm2niix_name:
                run = dcm2niix_name.split("run")[1]
                run = run[1:] if run[0] == "_" else run
                run = run.zfill(2)
                bids_dir, bids_name = self._switch_name(dcm2niix_name, run)
            else:
                bids_dir, bids_name = self._switch_name(dcm2niix_name)

            # Setup path to new BIDs directory
            bids_path = os.path.join(os.path.dirname(h_file), bids_dir)
            if not os.path.exists(bids_path):
                os.makedirs(bids_path)

            # Determine extension, move and rename json, nii files
            file_ext = (
                ".json"
                if os.path.splitext(h_file)[1] == ".json"
                else ".nii.gz"
            )
            shutil.move(h_file, f"{bids_path}/{bids_name}{file_ext}")

        # Check that bids org worked
        t1_list = sorted(glob.glob(f"{self._subj_raw}/anat/*T1w.nii.gz"))
        if not t1_list:
            raise FileNotFoundError("No BIDS-organized T1w files detected.")
        return t1_list

    def update_func(self):
        """Updated TaskName field of func JSON sidecars."""
        # Update func jsons with "TaskName" Field, account for task/rest
        print(
            f"\t\t\t\tUpdating func jsons for {self._subj}, {self._sess} ..."
        )
        func_json_all = sorted(glob.glob(f"{self._subj_raw}/func/*_bold.json"))
        if not func_json_all:
            raise ValueError(
                "No BIDS-organized func files found, try BidsifyNii.bids_nii"
            )
        for func_json in func_json_all:
            h_task = func_json.split("_task-")[1].split("_")[0]
            self._update_json(func_json, "TaskName", h_task)

    def update_fmap(self):
        """Updated Intended for field of fmap JSON sidecars."""
        print(
            f"\t\t\t\tUpdating fmap jsons for {self._subj}, {self._sess} ..."
        )

        # Get, validate list of fmap json files
        fmap_json_list = sorted(glob.glob(f"{self._subj_raw}/fmap/*json"))
        if not fmap_json_list:
            raise ValueError(
                "No BIDS-organized fmap files found, try BidsifyNii.bids_nii"
            )
        fmap_count = len(fmap_json_list)
        if fmap_count > 2:
            raise ValueError("More than 2 fmap images found!")

        # Get bold files
        try:
            bold_list = [
                x.split(f"{self._subj}/")[1]
                for x in sorted(
                    glob.glob(f"{self._subj_raw}/func/*bold.nii.gz")
                )
            ]
        except IndexError:
            raise ValueError(
                "No BIDS-organized func files found, try BidsifyNii.bids_nii"
            )

        # Update fmap jsons with intended lists - for old protocol (fmap==1)
        # assign all funcs to fmap. For new protocol (fmap==2) split runs
        # between two fmaps.
        if fmap_count == 1:
            self._update_json(fmap_json_list[0], "IntendedFor", bold_list)
        elif fmap_count == 2:
            # Manage special cases
            subid = self._subj.split("-")[1]
            map_bold_fmap = unique_cases.fmap_issue(
                self._sess, subid, bold_list
            )
            if map_bold_fmap:
                for fmap_json, map_bold in zip(fmap_json_list, map_bold_fmap):
                    self._update_json(fmap_json, "IntendedFor", map_bold)
                return

            # Regular cases -- ensure rest is at end of list
            rest_idx = [x for x, y in enumerate(bold_list) if "task-rest" in y]
            if rest_idx:
                bold_list.append(bold_list.pop(rest_idx[0]))
            map_bold_fmap = []
            map_bold_fmap.append(bold_list[:4])
            map_bold_fmap.append(bold_list[4:])
            for fmap_json, map_bold in zip(fmap_json_list, map_bold_fmap):
                self._update_json(fmap_json, "IntendedFor", map_bold)

    def _update_json(
        self,
        bids_json: Union[str, os.PathLike],
        field: str,
        values: Union[list, str],
    ):
        """Add, update field to BIDS JSON sidecar."""
        with open(bids_json) as jf:
            sidecar_dict = json.load(jf)
        sidecar_dict[field] = values
        with open(bids_json, "w") as jf:
            json.dump(sidecar_dict, jf)

    def _switch_name(self, dcm2niix_name: str, run: str = None) -> dict:
        """Return rawdata BIDS directory and file name."""
        # Key is from dcm2niix file names, value tuple contains
        # BIDS directory and file names. Manage new fmap
        # protocol names being called P_A_run1 and P_A_run_2.
        base_str = f"{self._subj}_{self._sess}"
        name_dict = {
            "DICOM_EmoRep_anat": ("anat", f"{base_str}_T1w"),
            f"DICOM_EmoRep_run{run}": (
                "func",
                f"{base_str}_{self._task}_run-{run}_bold",
            ),
            f"DICOM_Rest_run{run}": (
                "func",
                f"{base_str}_task-rest_run-{run}_bold",
            ),
            "DICOM_Field_Map_P_A": ("fmap", f"{base_str}_acq-rpe_dir-PA_epi"),
            "DICOM_Field_Map_P_A_run1": (
                "fmap",
                f"{base_str}_acq-rpe_dir-PA_run-{run}_epi",
            ),
            "DICOM_Field_Map_P_A_run_2": (
                "fmap",
                f"{base_str}_acq-rpe_dir-PA_run-{run}_epi",
            ),
        }
        return name_dict[dcm2niix_name]


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
