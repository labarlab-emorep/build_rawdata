"""Data-type-specific methods for EmoRep (Exp2_Compute_Emotion).

ProcessMRI  : manage MRI conversion
ProcessBeh  : manage emorep task responses
ProcessRate : manage resting endoresements
ProcessPhys : manage physio data

"""

import os
import re
import glob
import shutil
import subprocess as sp
from typing import Union
from datetime import datetime
import bioread  # noqa: F401
import neurokit2 as nk
from build_rawdata.resources import process
from build_rawdata.resources import bidsify
from build_rawdata.resources import behavior


# %%
class ProcessMri:
    """Convert DICOMs into NIfTIs and BIDS organize for single subject.

    Also supports defacing for NDAR hosting.

    Parameters
    ----------
    subid : str
        Subject ID
    raw_path : str, os.PathLike
        Location of rawdata

    Methods
    -------
    bids_nii()
        Convert DICOMs into NIfTI format, then BIDS oragnize
    deface_anat()
        Remove face of anatomical

    Example
    -------
    proc_mri = ProcessMri("ER0009", "/path/to/rawdata")
    cont_pipe, anat_list = proc_mri.bids_nii(
        "/path/to/ER0009/day2_movies/DICOM"
    )
    deface_path = proc_mri.deface_anat("/path/to/derivatives")

    """

    def __init__(self, subid, raw_path):
        """Initialize."""
        self._subid = subid
        self._subj = f"sub-{subid}"
        self._raw_path = raw_path

    def _organize_dcms(self):
        """Organize DICOMs according to protocol name."""
        chk_dir = os.path.join(self._dcm_source, "EmoRep_anat")
        if os.path.exists(chk_dir):
            return

        print(f"\t\tOrganizing DICOMs for {self._subj}, {self._sess} ...")
        sh_run = sp.Popen(
            f"org_dcms.sh -d {self._dcm_source}",
            shell=True,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        sh_out, sh_err = sh_run.communicate()
        sh_run.wait()
        if not os.path.exists(chk_dir):
            process.error_msg(
                "Missing expected output of bin/org_dcms.sh",
                sh_out.decode("utf-8"),
                sh_err.decode("utf-8"),
            )
            raise FileNotFoundError("No organized DICOMS found.")

    def bids_nii(self, dcm_source):
        """Convert sourcedata DICOMs to NIfTIs.

        Organizes DICOMs in dcm_source via bin/org_dcms.sh,
        then triggers process.dcm2niix. Finally, BIDS
        organize dcm2niix output.

        Parameters
        ----------
        dcm_source : str, os.PathLike
            Location of DICOM directory

        Returns
        -------
        tuple
            [0] = bool, list of dcm2niix output
                True = bidsified anat files found
                False = no dcms found
            [1] = None, list of bidsified anat nii
                if bidsification of niis was triggered

        """
        # Make niis, determine if pipeline through bidsification
        # should continue
        self._dcm_source = dcm_source
        cont_pipe = self._make_niftis()
        if isinstance(cont_pipe, list):
            anat_list = self._bidsify_niftis()
            return (cont_pipe, anat_list)
        return (cont_pipe, None)

    def _make_niftis(self) -> Union[bool, list]:
        """Organize dcms and trigger dcm2niix, return nii list."""
        # Determine session/task names
        sess_dir = os.path.basename(os.path.dirname(self._dcm_source))
        _day, _tname = sess_dir.split("_")
        self._sess = f"ses-{_day}"
        self._task = f"task-{_tname}"

        # Check for previous work, required files
        self._subj_raw = os.path.join(self._raw_path, self._subj, self._sess)
        if glob.glob(f"{self._subj_raw}/anat/*.nii.gz"):
            return True
        if not glob.glob(f"{self._dcm_source}/**/*.dcm", recursive=True):
            print(f"\tNo DICOMs found at {self._dcm_source}, skipping ...")
            return False

        # Organize DICOMs in sourcedata
        self._organize_dcms()

        # Setup, check for previous, and run dcm conversion
        print(f"\t\tMaking NIfTIs for {self._subj}, {self._sess} ...")
        if not os.path.exists(self._subj_raw):
            os.makedirs(self._subj_raw)
        nii_list, json_list = process.dcm2niix(
            self._dcm_source, self._subj_raw, self._subid
        )
        return nii_list

    def _bidsify_niftis(self) -> list:
        """BIDS-organize raw dcm2niix output, return anat list."""
        # Check for previous BIDS, run bidsify
        anat_list = glob.glob(f"{self._subj_raw}/anat/*.nii.gz")
        if anat_list:
            return anat_list

        print(f"\t\tBIDs-ifying NIfTIs for {self._subj}, {self._sess} ...")
        bn = bidsify.BidsifyNii(
            self._subj_raw, self._subj, self._sess, self._task
        )
        anat_list = bn.bids_nii()
        bn.update_func()
        bn.update_fmap()
        return anat_list

    def deface_anat(self, deriv_dir):
        """Deface BIDS-organized anat file.

        Parameters
        ----------
        deriv_dir : str, os.PathLike
            Location of derivatives directory

        Returns
        -------
        list
            Location of defaced output

        """
        if not hasattr(self, "_subj_raw") or not os.path.exists(
            os.path.join(self._subj_raw, "anat")
        ):
            raise RuntimeError(
                "ProcessMri.deface_anat requires ProcessMri.bids_nii "
                + "to be run first"
            )
        t1_list = sorted(glob.glob(f"{self._subj_raw}/anat/*T1w.nii.gz"))
        if not t1_list:
            raise FileNotFoundError(
                f"No T1w files detected in {self._subj_raw}/anat"
            )
        return process.deface(t1_list, deriv_dir, self._subid, self._sess)


# %%
class ProcessBeh:
    """Make BIDS-organized events sidecars for single subject.

    Convert EmoRep task output into events sidecars, organize in rawdata.

    Parameters
    ----------
    subid : str
        Subject ID
    raw_path : str, os.PathLike
        Location of rawdata

    Methods
    -------
    make_events()
        Generate events sidecars from task csv

    Example
    -------
    proc_beh = ProcessBeh("ER0009", "/path/to/rawdata")
    beh_tsv, beh_json = proc_beh.make_events(
        "/path/to/sourcedata/ER0009/run01.csv"
    )

    """

    def __init__(self, subid, raw_path):
        """Initialize."""
        self._subid = subid
        self._subj = f"sub-{subid}"
        self._raw_path = raw_path
        self._task_switch = {
            "movies": "scannermovieData",
            "scenarios": "scannertextData",
        }

    def _validate(self) -> bool:
        """Validate naming and organization of sourcedata task files."""
        # Get day, task, filename
        day = os.path.basename(
            os.path.dirname(os.path.dirname(self._task_path))
        )
        task = day.split("_")[1]
        task_file = os.path.basename(self._task_path)

        # Check file name
        try:
            _, chk_task, h_subid, h_sess, _, _ = task_file.split("_")
        except ValueError:
            print(
                f"ERROR: Improperly named task file : {task_file}s "
                + "skipping."
            )
            return False

        # Check task located in correct session
        if chk_task != self._task_switch[task]:
            print(
                f"\tERROR: Mismatch of task file '{chk_task}' with "
                + f"session '{day}', skipping."
            )
            return False

        # Check task belongs to subject
        chk_subid = h_subid[4:] if "sub" in h_subid else h_subid
        if chk_subid != self._subid:
            print(
                f"\tERROR: Task file for subject '{chk_subid}' found in "
                + f"sourcedata/{self._subid}/{day}/Scanner_behav, skipping."
            )
            return False

        # Check session and day alignment
        chk_sess = h_sess[4:] if "-" in h_sess else h_sess[3:]
        if chk_sess != day[:4]:
            print(
                f"\tERROR: File for '{chk_sess}' found in "
                + f"session '{day}', skipping."
            )
            return False
        return True

    def make_events(self, task_path):
        """Generate events sidecars from task csv.

        Parameters
        ----------
        task_path : str, os.PathLike
            Location of sourcedata task file

        Returns
        -------
        tuple
            [0] = Path to events.tsv
            [1] = Path to events.json

        """
        self._task_path = task_path
        if not self._validate():
            return

        # Setup sess, task, and run strings - deal with change
        # in naming format.
        task_file = os.path.basename(task_path)
        try:
            run = "run-0" + task_file.split("run-")[1].split("_")[0]
        except IndexError:
            run = "run-0" + task_file.split("run")[1].split("_")[0]
        day_task = task_path.split("day")[1].split("/")[0]
        _day, _tname = day_task.split("_")
        sess = f"ses-day{_day}"
        task = f"task-{_tname}"

        # Setup output location, make events sidecar
        subj_raw = os.path.join(self._raw_path, f"{self._subj}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        out_tsv = os.path.join(
            subj_raw, f"{self._subj}_{sess}_{task}_{run}_events.tsv"
        )
        out_json = out_tsv.replace("tsv", "json")
        if not os.path.exists(out_tsv):
            print(
                "\t\tMaking behavior events.tsv for "
                + f"{self._subj}, {sess} {run}"
            )
            out_tsv, out_json = behavior.events_tsv(
                task_path, subj_raw, self._subid, sess, task, run
            )
        return (out_tsv, out_json)


# %%
class ProcessRate:
    """Process post resting state endorsements for single subject.

    Parameters
    ----------
    subid : str
        Subject ID
    raw_path : str, os.PathLike
        Location of rawdata

    Methods
    -------
    make_rate()
        Organize post resting responses into rawdata beh

    Example
    -------
    proc_rest = ProcessRate("ER0009", "/path/to/rawdata")
    df, file_path = proc_rest.make_rate(
        "/path/to/sourcedata/ER0009/rest.csv"
    )

    """

    def __init__(self, subid, raw_path):
        """Initialize."""
        self._subid = subid
        self._subj = f"sub-{subid}"
        self._raw_path = raw_path

    def _validate(self) -> bool:
        """Validate naming and organization of sourcedata rest files."""
        day = os.path.basename(
            os.path.dirname(os.path.dirname(self._rate_path))
        )
        rate_file = os.path.basename(self._rate_path)

        # Check naming of rest file
        try:
            _, _, chk_subid, chk_sess, date_ext = rate_file.split("_")
        except ValueError:
            print(
                f"\tERROR: Improperly named rating file : {rate_file}, "
                + "skipping."
            )
            return False

        # Make sure data is in correct participant's location
        if chk_subid[4:] != self._subid:
            print(
                f"\tERROR: Rating file for subject '{chk_subid}' found "
                + f"in sourcedata/{self._subid}/{day}/Scanner_behav, skipping."
            )
            return False

        # Check alignment of sessions and task
        if chk_sess[4:] != day[:4]:
            print(
                f"\tERROR: File for '{chk_sess[4:]}' found in "
                + f"session : {day}, skipping."
            )
            return False
        return True

    def make_rate(self, rate_path):
        """Generate rest ratings beh files.

        Parameters
        ----------
        rate_path : str, os.PathLike
            Location of sourcedata rest ratings csv

        Returns
        -------
        tuple
            [0] = pd.DataFrame, None (output already existed)
            [1] = Location of file

        """
        self._rate_path = rate_path
        if not self._validate():
            return

        # Determine session, setup rawdata path
        rate_file = os.path.basename(rate_path)
        sess = "ses-" + rate_file.split("ses-")[1].split("_")[0]
        subj_raw = os.path.join(
            self._raw_path, f"sub-{self._subid}/{sess}/beh"
        )
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)

        # Clean file date
        _, _, chk_subid, chk_sess, date_ext = rate_file.split("_")
        h_date = date_ext.split(".")[0]
        date_time = datetime.strptime(h_date, "%m%d%Y")
        date_str = datetime.strftime(date_time, "%Y-%m-%d")
        out_file = os.path.join(
            subj_raw, f"sub-{self._subid}_{sess}_rest-ratings_{date_str}.tsv"
        )
        if os.path.exists(out_file):
            return (None, out_file)

        # Make rawdata file
        print("\t\tMaking rest ratings.tsv for " + f"{self._subj}, {sess} ...")
        return behavior.rest_ratings(rate_path, self._subid, sess, out_file)


# %%
class ProcessPhys:
    """Manage physio files collected alongside fMRI for single subject.

    Both copy and acq and convert into a txt format, write out
    to rawdata location.

    Parameters
    ----------
    subid : str
        Subject ID
    raw_path : str, os.PathLike
        Location of rawdata

    Methods
    -------
    make_physio()
        Copy acq and generate txt

    Example
    -------
    proc_phys = ProcessPhys("ER0009", "/path/to/rawdata")
    proc_phys.make_physio("/path/to/sourcedata/ER0009/phys.acq")

    """

    def __init__(self, subid, raw_path):
        """Initialize."""
        self._subid = subid
        self._raw_path = raw_path

    def _validate(self) -> bool:
        """Validate naming and organization of sourcedata physio files."""
        day = os.path.basename(
            os.path.dirname(os.path.dirname(self._phys_path))
        )
        phys_file = os.path.basename(self._phys_path)

        # Check naming of file
        try:
            chk_subid, chk_a, chk_b, _ = phys_file.split("_")
        except ValueError:
            print(
                f"ERROR: Improperly named physio file : {phys_file}, "
                + "skipping."
            )
            return False

        # Check match of subject to data
        if chk_subid != self._subid:
            print(
                f"\tERROR: Physio file for subject '{chk_subid}' found "
                + f"in sourcedata/{self._subid}/{day}/Scanner_physio, "
                + "skipping."
            )
            return False

        # Check match of day and session
        chk_day = chk_a if "day" in chk_a else chk_b
        if chk_day != day[:4]:
            print(
                f"\tERROR: File for '{chk_day}' found in "
                + f"session : {day}, skipping."
            )
            return False
        return True

    def make_physio(self, phys_path):
        """Convert acq to txt format.

        Parameters
        ----------
        phys_path : str, os.PathLike
            Location of sourcedata physio file

        Returns
        -------
        str, os.PathLike
            Location of output physio file

        """
        self._phys_path = phys_path
        if not self._validate():
            return

        # Get session, task strings
        sess_task = phys_path.split("day")[1].split("/")[0]
        _day, _tname = sess_task.split("_")
        sess = f"ses-day{_day}"
        task = f"task-{_tname}"

        # Get run, deal with resting task
        if "run" in phys_path:
            run = "run-0" + phys_path.split("_run")[1].split(".")[0]
        else:
            run = "run-01"
            task = "task-rest"

        # Setup output dir/name
        subj_phys = os.path.join(
            self._raw_path, f"sub-{self._subid}/{sess}/phys"
        )
        if not os.path.exists(subj_phys):
            os.makedirs(subj_phys)
        dest_orig = os.path.join(subj_phys, os.path.basename(phys_path))
        dest_acq = os.path.join(
            subj_phys,
            f"sub-{self._subid}_{sess}_{task}_{run}_"
            + "recording-biopack_physio.acq",
        )

        # Generate tsv dataframe and copy data
        if os.path.exists(dest_acq):
            return dest_acq
        print(
            "\t\tProcessing physio files for "
            + f"sub-{self._subid}, {sess} {run} {task}"
        )
        try:
            df_phys, _ = nk.read_acqknowledge(phys_path)
            df_phys = df_phys.round(6)
            df_phys.to_csv(
                re.sub(".acq$", ".txt", dest_acq),
                header=False,
                index=False,
                sep="\t",
            )
            shutil.copy(phys_path, dest_orig)
            os.rename(dest_orig, dest_acq)
            return dest_acq
        except:  # noqa: E722, nk throws the stupid struct.error
            "\t\t\tInsufficient data, continuing ..."
            return
