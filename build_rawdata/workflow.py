"""Coordinate modules into workflow.

ConvertSourcedata is used to check for data and
validate proper organization. It then triggers
the respective helper class according to the
method executed.

"""
# %%
import os
import re
import glob
import shutil
import subprocess as sp
from typing import Union
from fnmatch import fnmatch
from datetime import datetime
import bioread  # noqa: F401
import neurokit2 as nk
from build_rawdata.resources import process, bidsify, behavior


# %%
class _ProcessMri:
    """Convert DICOMs into NIfTIs and BIDS organize.

    Also supports defacing for NDAR hosting.

    Methods
    -------
    make_niftis(dcm_source)
        Convert DICOMs into NIfTI format
    bidsify_niftis()
        BIDS-organize rawdata NIfTIs
    deface_anat(deriv_dir)
        Remove face of anatomical

    Example
    -------
    pm = _ProcessMri("ER0009", "/path/to/rawdata")
    pm.make_niftis("/path/to/ER0009/day2_movies/DICOM")
    pm.bidsify_niftis()
    pm.deface_anat("/path/to/derivatives")

    """

    def __init__(self, subid: str, raw_path: Union[str, os.PathLike]):
        """Initialize."""
        print("\tInitializing _ProcessMri")
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

    def make_niftis(self, dcm_source: Union[str, os.PathLike]):
        """Convert sourcedata DICOMs to NIfTIs.

        Organizes DICOMs in dcm_source via bin/org_dcms.sh,
        then triggers process.dcm2niix.

        """
        # Determine session/task names and organize DICOMs
        self._dcm_source = dcm_source
        sess_dir = os.path.basename(os.path.dirname(dcm_source))
        _day, _tname = sess_dir.split("_")
        self._sess = f"ses-{_day}"
        self._task = f"task-{_tname}"
        self._organize_dcms()

        # Setup, check for previous, and run dcm conversion
        print(f"\t\tMaking NIfTIs for {self._subj}, {self._sess} ...")
        self._subj_raw = os.path.join(self._raw_path, self._subj, self._sess)
        if not os.path.exists(self._subj_raw):
            os.makedirs(self._subj_raw)

        chk_anat = glob.glob(f"{self._subj_raw}/anat/*.nii.gz")
        if chk_anat:
            return
        process.dcm2niix(dcm_source, self._subj_raw, self._subid, self._sess)

    def bidsify_niftis(self):
        """BIDS-organize raw dcm2niix output."""
        if not hasattr(self, "_subj_raw") or not hasattr(self, "_sess"):
            raise AttributeError(
                "_ProcessMri.bidsify_niftis requires _ProcessMri.make_niftis"
                + " to be run first."
            )

        # Check for previous BIDS, run bidsify
        chk_bids = glob.glob(f"{self._subj_raw}/anat/*.nii.gz")
        if chk_bids:
            return

        print(f"\t\tBIDs-ifying NIfTIs for {self._subj}, {self._sess} ...")
        bn = bidsify.BidsifyNii(
            self._subj_raw, self._subj, self._sess, self._task
        )
        bn.bids_nii()
        bn.update_func()
        bn.update_fmap()

    def deface_anat(self, deriv_dir: Union[str, os.PathLike]):
        """Deface BIDS-organized anat file."""
        if not hasattr(self, "_subj_raw") or not os.path.exists(
            os.path.join(self._subj_raw, "anat")
        ):
            raise RuntimeError(
                "_ProcessMri.deface_anat requires both _ProcessMri.make_niftis"
                + " and _ProcessMri.bidsify_niftis to be run first"
            )
        t1_list = sorted(glob.glob(f"{self._subj_raw}/anat/*T1w.nii.gz"))
        if not t1_list:
            raise FileNotFoundError(
                f"No T1w files detected in {self._subj_raw}/anat"
            )
        print(f"\t\tDefacing anats for {self._subj} ...")
        _ = process.deface(t1_list, deriv_dir, self._subid, self._sess)


# %%
class _ProcessBeh:
    """Make BIDS-organized events sidecars.

    Convert EmoRep task output into events sidecars, organize in rawdata.

    Methods
    -------
    make_events(task_path)
        Generate events sidecar from task csv

    Example
    -------
    pb = _ProcessBeh("ER0009", "/path/to/rawdata")
    pb.make_events("/path/to/sourcedata/ER0009/run01.csv")

    """

    def __init__(self, subid: str, raw_path: Union[str, os.PathLike]):
        """Initialize."""
        print("\tInitializing _ProcessBeh")
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

    def make_events(self, task_path: Union[str, os.PathLike]):
        """Generate events sidecars from task csv."""
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
        print(
            "\t\tMaking behavior events.tsv for "
            + f"{self._subj}, {sess} {run}"
        )
        subj_raw = os.path.join(self._raw_path, f"{self._subj}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        out_file = os.path.join(
            subj_raw, f"{self._subj}_{sess}_{task}_{run}_events.tsv"
        )
        if not os.path.exists(out_file):
            behavior.events_tsv(
                task_path, subj_raw, self._subid, sess, task, run
            )


# %%
class _ProcessRate:
    """Process post resting state endorsements.

    Methods
    -------
    make_rate(rate_path)
        Organize post resting responses into rawdata beh

    Example
    -------
    pr = _ProcessRate("ER0009", "/path/to/rawdata")
    pr.make_rate("/path/to/sourcedata/ER0009/rest.csv")

    """

    def __init__(self, subid: str, raw_path: Union[str, os.PathLike]):
        """Initialize."""
        print("\tInitializing _ProcessRate")
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

    def make_rate(self, rate_path: Union[str, os.PathLike]):
        """Generate rest ratings beh files."""
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

        # Make rawdata file
        print("\t\tMaking rest ratings.tsv for " + f"{self._subj}, {sess} ...")
        out_file = os.path.join(
            subj_raw, f"sub-{self._subid}_{sess}_rest-ratings_{date_str}.tsv"
        )
        if not os.path.exists(out_file):
            _ = behavior.rest_ratings(
                rate_path, subj_raw, self._subid, sess, out_file
            )


# %%
class _ProcessPhys:
    """Manage physio files collected alongside fMRI.

    Both copy and acq and convert into a txt format, write out
    to rawdata location.

    Methods
    -------
    make_physio(phys_path)
        Copy acq and generate txt

    Example
    -------
    pp = _ProcessPhys("ER0009", "/path/to/rawdata", "/path/to/derivatives")
    pb.make_physio("/path/to/sourcedata/ER0009/phys.acq")

    """

    def __init__(
        self,
        subid: str,
        raw_path: Union[str, os.PathLike],
        deriv_dir: Union[str, os.PathLike],
    ):
        """Initialize."""
        print("\tInitializing _ProcessPhys")
        self._subid = subid
        self._raw_path = raw_path
        self._deriv_dir = deriv_dir

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

    def make_physio(self, phys_path: Union[str, os.PathLike]):
        """Convert acq to txt format."""
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
        print(
            "\t\tProcessing physio files for "
            + f"sub-{self._subid}, {sess} {run} {task}"
        )
        subj_phys = os.path.join(
            self._raw_path, f"sub-{self._subid}/{sess}/phys"
        )
        subj_deriv = os.path.join(
            self._deriv_dir, "scr_autonomate", f"sub-{self._subid}/{sess}"
        )
        for h_dir in [subj_phys, subj_deriv]:
            if not os.path.exists(h_dir):
                os.makedirs(h_dir)
        dest_orig = os.path.join(subj_phys, os.path.basename(phys_path))
        dest_acq = os.path.join(
            subj_phys,
            f"sub-{self._subid}_{sess}_{task}_{run}_"
            + "recording-biopack_physio.acq",
        )

        # Generate tsv dataframe and copy data
        if os.path.exists(dest_acq):
            return
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
        except:  # noqa: E722, nk throws the stupid struct.error
            "\t\t\tInsufficient data, continuing ..."
            return


# %%
class ConvertSourcedata:
    """Conduct DICOM conversion worklow.

    Coordinate resources for MRI conversion, BIDSification,
    generating events sidecars, and moving physio data.
    Validate organization of sourcedata.

    Methods
    -------
    chk_sourcedata(subid)
        Check for basic organization of subject sourcedata
    convert_mri()
        Convert MRI sourcedata to BIDS-formatted rawdata
    convert_beh()
        Make BIDS events sidecars
    convert_rate()
        Process post resting state endorsements
    convert_phys()
        Copy and make txt from acq file

    Example
    -------
    cs = ConvertSourcedata(
        "/path/to/sourcedata",
        "/path/to/rawdata",
        "/path/to/derivatives",
        True,
    )
    cs.chk_sourcedata("ER0909")
    cs.convert_mri()
    cs.convert_beh()
    cs.convert_phys()
    cs.convert_rate()

    Notes
    -----
    Order is important, chk_sourcedata() needs to be executed first and
    convert_mri() needs to be executed second.

    """

    def __init__(self, source_path, raw_path, deriv_dir, do_deface):
        """Initialize.

        Parameters
        ----------
        source_path : path
            Location of project sourcedata
        raw_path : path
            Location of project rawdata
        deriv_dir : path
            Location of project derivatives
        do_deface : bool
            Whether to deface T1w files

        """
        print("Initializing ConvertSourcedata")
        self._source_path = source_path
        self._raw_path = raw_path
        self._deriv_dir = deriv_dir
        self._do_deface = do_deface

    def chk_sourcedata(self, subid):
        """Validate sourcedata organization.

        Parameters
        ----------
        subid : str
            Subject identifier in sourcedata

        Returns
        -------
        bool
            If basic check passed

        """
        print("\tChecking sourcedata session names ...")
        self._subid = subid

        # Check for session data
        subj_source = os.path.join(self._source_path, subid)
        sess_list = [x for x in os.listdir(subj_source) if fnmatch(x, "day*")]
        if not sess_list:
            print(
                "\tNo sourcedata properly named session directories "
                + "detected, skipping."
            )
            return False

        # Check naming of session data
        for sess in sess_list:
            try:
                day, task = sess.split("_")
            except ValueError:
                print(
                    "\tERROR: Incorrect sourcedata session directory "
                    + f"name : {sess}"
                )
                return False
            if len(day) != 4 or not (task == "movies" or task == "scenarios"):
                print(
                    "\tERROR: Incorrect sourcedata session directory "
                    + f"name : {sess}"
                )
                return False
        return True

    def convert_mri(self):
        """Trigger conversion of MRI data."""
        dcm_list = sorted(
            glob.glob(f"{self._source_path}/{self._subid}/day*/DICOM")
        )
        if not dcm_list:
            print(
                "\tNo properly organized DICOMs detected for "
                + f"sub-{self._subid}. Skipping."
            )
            return

        # Process MRI data
        mk_mri = _ProcessMri(self._subid, self._raw_path)
        for dcm_source in dcm_list:
            chk_dcm = glob.glob(f"{dcm_source}/**/*.dcm", recursive=True)
            if not chk_dcm:
                print(f"\tNo DICOMs found at {dcm_source}, skipping ...")
                continue

            # Make NIfTI, bidsify, and deface
            mk_mri.make_niftis(dcm_source)
            mk_mri.bidsify_niftis()
            if self._do_deface:
                mk_mri.deface_anat(self._deriv_dir)

    def convert_beh(self):
        """Trigger conversion of behavioral data."""
        beh_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*"
                + "/Scanner_behav/*run*csv"
            )
        )
        if not beh_list:
            print(
                "\tNo properly organized task files detected for "
                + f"sub-{self._subid}. Skipping."
            )
            return

        # Deal with update to resting state name
        beh_list = [x for x in beh_list if "Rest" not in x]
        mk_beh = _ProcessBeh(self._subid, self._raw_path)
        for task_path in beh_list:
            mk_beh.make_events(task_path)

    def convert_rate(self):
        """Trigger conversion of post-rest endorsement ratings."""
        rate_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*/"
                + "Scanner_behav/*RestRating*csv"
            )
        )
        if not rate_list:
            print(
                "\tNo properly organized rest rating files detected for "
                + f"sub-{self._subid}, skipping."
            )
            return
        elif len(rate_list) > 2:
            print(
                f"\tExpected two rest rating files, found :\n\t{rate_list},"
                + " skipping"
            )
            return

        # Convert all rest ratings
        mk_rate = _ProcessRate(self._subid, self._raw_path)
        for rate_path in rate_list:
            mk_rate.make_rate(rate_path)

    def convert_phys(self):
        """Trigger conversion of physiology data."""
        phys_dirs = sorted(
            glob.glob(f"{self._source_path}/{self._subid}/day*/Scanner_physio")
        )
        if not phys_dirs:
            print(
                f"\tNo physio files detected for sub-{self._subid}, skipping."
            )
            return

        # Convert all physio files
        phys_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*/Scanner_physio/*acq"
            )
        )
        if not phys_list:
            print(
                "\tNo properly organized physio files detected for "
                + f"sub-{self._subid}, skipping."
            )
            return
        mk_phys = _ProcessPhys(self._subid, self._raw_path, self._deriv_dir)
        for phys_path in phys_list:
            mk_phys.make_physio(phys_path)
