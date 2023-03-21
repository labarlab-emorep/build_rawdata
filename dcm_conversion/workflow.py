"""Coordinate modules into workflow."""
# %%
import os
import re
import glob
import shutil
import subprocess as sp
from fnmatch import fnmatch
from datetime import datetime
import bioread  # left here for generatings requirements files
import neurokit2 as nk
from dcm_conversion.resources import process, bidsify, behavior


# %%
def _split(sess_task, subid):
    """Split string for session and task.

    Parameters
    ----------
    sess_task : str
        Contains session and task separated by underscore
    subid : str
        Subject idenfier

    Raises
    ------
    ValueError, FileNotFoundError
        If errors exist in directory organization or naming

    Returns
    -------
    tuple
        [0] session string, or None
        [1] task string, or None

    """
    try:
        sess, task = sess_task.split("_")
        sess_check = True if len(sess) == 8 else False
        task_check = True if task == "movies" or task == "scenarios" else False
        if not sess_check or not task_check:
            raise FileNotFoundError
        return (sess, f"task-{task}")
    except (ValueError, FileNotFoundError):
        print(
            f"""
            Improper session name for {subid}: {sess_task[4:]}
            \tSkipping session ...
            """
        )
        return (None, None)


# %%
class _ProcessMri:
    """Convert DICOMs into NIfTIs and BIDS organize.

    Also supports defacing for NDAR hosting.

    Methods
    -------
    make_niftis(dcm_source)
    bidsify_niftis()
    deface_anat(deriv_dir)

    Example
    -------
    pm = _ProcessMri("ER0009", "/path/to/rawdata")
    pm.make_niftis("/path/to/ER0009/day2_movies/DICOM")
    pm.bidsify_niftis()
    pm.deface_anat("/path/to/derivatives")

    """

    def __init__(self, subid, raw_path):
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

    def make_niftis(self, dcm_source):
        """Convert sourcedata DICOMs to NIfTIs.

        Organizes DICOMs in dcm_source via bin/org_dcms.sh,
        then triggers process.dcm2niix.

        Parameters
        ----------
        dcm_source : str, os.PathLike
            Path to participant's DICOM directgory

        """
        # Determine session/task names and organize DICOMs
        self._dcm_source = dcm_source
        sess_dir = os.path.basename(os.path.dirname(dcm_source))
        _day, _tname = sess_dir.split("_")
        self._sess = f"ses-{_day}"
        self._task = f"task-{_tname}"
        self._organize_dcms()

        #
        print(f"\t\tMaking NIfTIs for {self._subj}, {self._sess} ...")
        self._subj_raw = os.path.join(self._raw_path, self._subj, self._sess)
        if not os.path.exists(self._subj_raw):
            os.makedirs(self._subj_raw)

        # Check for previous BIDS
        chk_anat = glob.glob(f"{self._subj_raw}/anat/*.nii.gz")
        if chk_anat:
            return
        process.dcm2niix(dcm_source, self._subj_raw, self._subid, self._sess)

    def bidsify_niftis(self):
        """BIDS-organize raw dcm2niix output."""
        if not hasattr(self, "_subj_raw") or not hasattr(self, "_sess"):
            raise AttributeError(
                "_ProcessMri.bidsify_niftis requires _ProcessMri.make_niftis"
                + f" to be run first."
            )

        # Check for previous BIDS
        chk_bids = glob.glob(f"{self._subj_raw}/fmap/*.nii.gz")
        if chk_bids:
            return

        #
        bn = bidsify.BidsifyNii(
            self._subj_raw, self._subj, self._sess, self._task
        )
        bn.bids_nii()
        bn.update_func()
        bn.update_fmap()

    def deface_anat(self, deriv_dir):
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
        _ = process.deface(t1_list, deriv_dir, self._subid, self._sess)


# %%
def _process_beh(source_path, raw_path, subid):
    """Make events files for subject.

    Validate organization of Scanner_behav then generate BIDS-compliant
    events tsv and json files for the movie and scenario tasks.

    Parameters
    ----------
    source_path : path
        Location of project sourcedata
    raw_path : path
        Location of subject's rawdata directory
    subid : str
        Subject identifier

    Returns
    -------
    None, True
        None = participant does not have properly-organized behavior data
        True = all processing occured successfully

    Notes
    -----
    Skips participant if task files are not detected or properly organized,
    named incorrectly, located in the wrong session, are from the wrong
    participant, or located in the wrong task.

    """
    print("\tProcessing task behavior data ...")

    # Set session, task name map
    task_switch = {
        "movies": "scannermovieData",
        "scenarios": "scannertextData",
    }

    # Check for Scanner_behav dir
    task_list = sorted(glob.glob(f"{source_path}/{subid}/day*/Scanner_behav"))
    if not task_list:
        print(
            "\tNo properly organized task files detected for "
            + f"sub-{subid}. Skipping."
        )
        return

    # Create events files for all task runs
    beh_list = sorted(
        glob.glob(f"{source_path}/{subid}/day*/Scanner_behav/*run*csv")
    )
    if not beh_list:
        print(
            "\tNo properly organized task files detected for "
            + f"sub-{subid}. Skipping."
        )
        return
    for task_path in beh_list:

        # Check that file is in correct location, deal with different
        # naming conventions.
        day = os.path.basename(os.path.dirname(os.path.dirname(task_path)))
        task = day.split("_")[1]
        task_file = os.path.basename(task_path)
        try:
            _, chk_task, h_subid, h_sess, _, _ = task_file.split("_")
        except ValueError:
            print(
                f"ERROR: Improperly named task file : {task_file}s "
                + "skipping."
            )
            continue
        if chk_task != task_switch[task]:
            print(
                f"\tERROR: Mismatch of task file '{chk_task}' with "
                + f"session '{day}', skipping."
            )
            continue
        chk_subid = h_subid[4:] if "sub" in h_subid else h_subid
        if chk_subid != subid:
            print(
                f"\tERROR: Task file for subject '{chk_subid}' found "
                + f"in sourcedata/{subid}/{day}/Scanner_behav, skipping."
            )
            continue
        chk_sess = h_sess[4:] if "-" in h_sess else h_sess[3:]
        if chk_sess != day[:4]:
            print(
                f"\tERROR: File for '{chk_sess}' found in "
                + f"session '{day}', skipping."
            )
            continue

        # Setup sess, task, and run strings - deal with change
        # in naming format.
        try:
            run = "run-0" + task_path.split("run-")[1].split("_")[0]
        except IndexError:
            run = "run-0" + task_path.split("run")[1].split("_")[0]
        sess_task = "ses-day" + task_path.split("day")[1].split("/")[0]
        sess, task = _split(sess_task, subid)
        if not sess:
            continue

        # Make func events sidecars
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        out_file = os.path.join(
            subj_raw, f"sub-{subid}_{sess}_{task}_{run}_events.tsv"
        )
        if not os.path.exists(out_file):
            print(f"\t Making events file for {task}, {run} ...")
            _, _ = behavior.events(task_path, subj_raw, subid, sess, task, run)

    return True


# %%
def _process_rate(source_path, raw_path, subid):
    """Make rest rating files for subject.

    Validate organization of resting state ratings then generates a
    BIDsy tsv in rawdata/subj/sess/beh of participant responses.

    Parameters
    ----------
    source_path : path
        Location of project sourcedata
    raw_path : path
        Location of subject's rawdata directory
    subid : str
        Subject identifier

    Returns
    -------
    None, True
        None = participant does not have properly-organized rest resposnes
        True = all processing occured successfully

    Raises
    ------
    FileExistsError
        When more thatn 2 rating files exist
    FileNotFoundError
        When sourcedata file is missing

    Notes
    -----
    Skips participant if rest files are not detected or properly organized,
    named incorrectly, located in the wrong session, or are from the wrong
    participant.

    """
    print("\tProcessing rest rating data ...")

    # Check for Scanner_behav dir
    task_list = sorted(glob.glob(f"{source_path}/{subid}/day*/Scanner_behav"))
    if not task_list:
        print(
            "\tNo properly organized rest rating files detected "
            + f"for sub-{subid}, skipping."
        )
        return

    # Check rest rating files
    rate_list = sorted(
        glob.glob(f"{source_path}/{subid}/day*/Scanner_behav/*RestRating*csv")
    )
    if not rate_list:
        print(
            "\tNo properly organized rest rating files detected for "
            + f"sub-{subid}, skipping."
        )
        return
    elif len(rate_list) > 2:
        print(
            f"\tExpected two rest rating files, found :\n\t{rate_list},"
            + " skipping"
        )
        return

    # Convert all rest ratings
    for rate_path in rate_list:

        # Check that file is in correct location
        day = os.path.basename(os.path.dirname(os.path.dirname(rate_path)))
        rate_file = os.path.basename(rate_path)
        try:
            _, _, chk_subid, chk_sess, date_ext = rate_file.split("_")
        except ValueError:
            print(
                f"\tERROR: Improperly named rating file : {rate_file}, "
                + "skipping."
            )
            continue
        if chk_subid[4:] != subid:
            print(
                f"\tERROR: Rating file for subject '{chk_subid}' found "
                + f"in sourcedata/{subid}/{day}/Scanner_behav, skipping."
            )
            continue
        if chk_sess[4:] != day[:4]:
            print(
                f"\tERROR: File for '{chk_sess[4:]}' found in "
                + f"session : {day}, skipping."
            )
            continue

        # Determine session
        rate_file = os.path.basename(rate_path)
        sess = "ses-" + rate_file.split("ses-")[1].split("_")[0]

        # Determine, setup rawdata path
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/beh")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)

        # Clean file date
        h_date = date_ext.split(".")[0]
        date_time = datetime.strptime(h_date, "%m%d%Y")
        date_str = datetime.strftime(date_time, "%Y-%m-%d")

        # Make rawdata file
        out_file = os.path.join(
            subj_raw, f"sub-{subid}_{sess}_rest-ratings_{date_str}.tsv"
        )
        if not os.path.exists(out_file):
            print(f"\t Making resting rate file for {sess} ...")
            _ = behavior.rest_ratings(
                rate_path, subj_raw, subid, sess, out_file
            )

    return True


# %%
def _process_phys(source_path, raw_path, deriv_dir, subid):
    """Copy physio files.

    Rename physio files to BIDS convention, organize them
    within subject session directories. Generate a tsv with
    txt extension for Autonomate with values rounded to 6
    decimals. Validate organization.

    Parameters
    ----------
    source_path : path
        Location of project sourcedata
    raw_path : path
        Location of project rawdata
    deriv_dir : path
        Location of derivatives directory
    subid : str
        Subject identifier

    Returns
    -------
    None, True
        None = participant does not have properly-organized physio data
        True = all processing occured successfully

    Notes
    -----
    Skips participant if physio files are not detected or properly organized,
    named incorrectly, located in the wrong session, or are from the wrong
    participant.

    """
    print("\tProcessing physio data ...")

    # Check for Scanner_physio dir
    phys_dirs = sorted(glob.glob(f"{source_path}/{subid}/day*/Scanner_physio"))
    if not phys_dirs:
        print(f"\tNo physio files detected for sub-{subid}, skipping.")
        return

    # Convert all physio files
    phys_list = sorted(
        glob.glob(f"{source_path}/{subid}/day*/Scanner_physio/*acq")
    )
    if not phys_list:
        print(
            "\tNo properly organized physio files detected for "
            + f"sub-{subid}, skipping."
        )
        return
    for phys_path in phys_list:

        # Check that file is in correct location, account for
        # different naming conventions.
        day = os.path.basename(os.path.dirname(os.path.dirname(phys_path)))
        phys_file = os.path.basename(phys_path)
        try:
            chk_subid, chk_a, chk_b, _ = phys_file.split("_")
        except ValueError:
            print(
                f"ERROR: Improperly named physio file : {phys_file}, "
                + "skipping."
            )
            continue
        if chk_subid != subid:
            print(
                f"\tERROR: Physio file for subject '{chk_subid}' found "
                + f"in sourcedata/{subid}/{day}/Scanner_physio, skipping."
            )
            continue
        chk_day = chk_a if "day" in chk_a else chk_b
        if chk_day != day[:4]:
            print(
                f"\tERROR: File for '{chk_day}' found in "
                + f"session : {day}, skipping."
            )
            continue

        # Get session, task strings
        sess_task = "ses-day" + phys_path.split("day")[1].split("/")[0]
        sess, h_task = _split(sess_task, subid)
        if not sess:
            continue

        # Get run, deal with resting task
        if "run" in phys_path:
            run = "run-0" + phys_path.split("_run")[1].split(".")[0]
            task = h_task
        else:
            run = "run-01"
            task = "task-rest"

        # Setup output dir/name
        subj_phys = os.path.join(raw_path, f"sub-{subid}/{sess}/phys")
        subj_deriv = os.path.join(
            deriv_dir, "scr_autonomate", f"sub-{subid}/{sess}"
        )
        for h_dir in [subj_phys, subj_deriv]:
            if not os.path.exists(h_dir):
                os.makedirs(h_dir)
        dest_orig = os.path.join(subj_phys, os.path.basename(phys_path))
        dest_acq = os.path.join(
            subj_phys,
            f"sub-{subid}_{sess}_{task}_{run}_recording-biopack_physio.acq",
        )

        # Generate tsv dataframe and copy data
        if not os.path.exists(dest_acq):
            print(f"\t Converting {sess} physio data : {task} {run}")
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
            except:
                # nk throws the stupid struct.error, hence the naked catch.
                "\t\t Insufficient data, continuing ..."
                continue

    return True


# %%
def dcm_worflow(
    subid,
    source_path,
    raw_path,
    deriv_dir,
    do_deface,
):
    """Conduct DICOM conversion worklow.

    Coordinate resources for MRI conversion, BIDSification,
    generating events sidecars, and moving physio data.
    Validate organization of sourcedata.

    Parameters
    ----------
    subid : str
        Subject identifier in sourcedata
    source_path : path
        Location of project sourcedata
    raw_path : path
        Location of project rawdata
    deriv_dir : path
        Location of project derivatives
    do_deface : bool
        Whether to deface T1w files

    Returns
    -------
    bool
        Whether all processing finished successfully


    Notes
    -----
    Skips participant sourcedata is not setup or session directories
    are improperly named.

    """
    print(f"\nProcessing data for {subid} ...")

    # Validate sourcedata session names
    print("\tChecking sourcedata session names ...")
    subj_source = os.path.join(source_path, subid)
    sess_list = [x for x in os.listdir(subj_source) if fnmatch(x, "day*")]
    if not sess_list:
        print(
            "\tNo sourcedata properly named session directories "
            + "detected, skipping."
        )
        return False
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

    # Get DICOM directory paths
    dcm_list = sorted(glob.glob(f"{source_path}/{subid}/day*/DICOM"))
    if not dcm_list:
        print(
            f"\tNo properly organized DICOMs detected for sub-{subid}. "
            + "Skipping."
        )
        return False

    # Process MRI data
    mk_mri = _ProcessMri(subid, raw_path)
    for dcm_source in dcm_list:
        chk_dcm = glob.glob(f"{dcm_source}/**/*.dcm", recursive=True)
        if not chk_dcm:
            print(f"\tNo DICOMs found at {dcm_source}, skipping ...")
            continue

        # Make NIfTI, bidsify, and deface
        mk_mri.make_niftis(dcm_source)
        mk_mri.bidsify_niftis()
        if do_deface:
            mk_mri.deface_anat(deriv_dir)

    return
    _ = _process_beh(source_path, raw_path, subid)
    _ = _process_rate(source_path, raw_path, subid)
    _ = _process_phys(source_path, raw_path, deriv_dir, subid)
    print(f"\t Done processing data for {subid}.")
    return True
