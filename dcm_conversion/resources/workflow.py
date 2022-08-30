"""Coordinate modules into workflow."""
import os
import glob
import shutil
from dcm_conversion.resources import process, bidsify, behavior


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
def _process_mri(dcm_list, raw_path, deriv_dir, subid, do_deface):
    """Convert DICOMs for subject.

    Parameters
    ----------
    dcm_list : list
        Paths to sourcedata DICOM directories
    raw_path : path
        Location of subject's rawdata
    deriv_dir : path
        Location of derivatives directory
    subid : str
        Subject identifier
    do_deface : bool
        Whether to deface T1w files

    Returns
    -------
    None

    """
    for subj_source in dcm_list:

        # Setup sess, task strings
        sess_task = "ses-day" + subj_source.split("day")[1].split("/")[0]
        sess, task = _split(sess_task, subid)
        if not sess:
            continue

        # Check for data
        try:
            os.listdir(subj_source)[0]
        except IndexError:
            print(f"No DICOMs detected for sub-{subid}, {sess}. Skipping.")
            continue

        # Setup subject rawdata, run dcm2niix
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)

        # Check for existing niis, run dcm2niix, bidsify
        print(f"\t Converting DICOMs for sub-{subid}, {sess} ...")
        t1_list = sorted(glob.glob(f"{subj_raw}/anat/*T1w.nii.gz"))
        if not t1_list:
            nii_list, json_list = process.dcm2niix(
                subj_source, subj_raw, subid, sess
            )
            t1_list = bidsify.bidsify_nii(
                nii_list, json_list, subj_raw, subid, sess, task
            )

        # Run defacing
        if do_deface:
            _ = process.deface(t1_list, deriv_dir, subid, sess)
        print("\t Done!")


# %%
def _process_beh(beh_list, raw_path, subid):
    """Make events files for subject.

    Parameters
    ----------
    beh_list : list
        Paths to task csv files
    raw_path : path
        Location of subject's rawdata directory
    subid : str
        Subject identifier

    Returns
    -------
    None

    """
    for task_file in beh_list:

        # Setup sess, task, and run strings
        try:
            run = "run-0" + task_file.split("run-")[1].split("_")[0]
        except IndexError:
            run = "run-0" + task_file.split("run")[1].split("_")[0]
        sess_task = "ses-day" + task_file.split("day")[1].split("/")[0]
        sess, task = _split(sess_task, subid)
        if not sess:
            continue

        # Make func events sidecars
        print(f"\t Making events file for {task}, {run} ...")
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        _, _ = behavior.events(task_file, subj_raw, subid, sess, task, run)


# %%
def _process_phys(phys_list, raw_path, subid):
    """Copy physio files.

    Rename physio files to BIDS convention, organize them
    within subject session directories.

    Parameters
    ----------
    phys_list : list
        Acq files
    raw_path : path
        Location of project rawdata
    subid : str
        Subject identifier

    Returns
    -------
    None

    """
    print("\t Copying physio files ...")
    for phys_file in phys_list:

        # Get session, task strings
        sess_task = "ses-day" + phys_file.split("day")[1].split("/")[0]
        sess, h_task = _split(sess_task, subid)
        if not sess:
            continue

        # Get run, deal with resting task
        if "run" in phys_file:
            run = "run-0" + phys_file.split("_run")[1].split(".")[0]
        else:
            run = "run-01"
            task = "task-rest"

        # Setup output dir/name
        subj_phys = os.path.join(raw_path, f"sub-{subid}/{sess}/phys")
        if not os.path.exists(subj_phys):
            os.makedirs(subj_phys)
        dest_orig = os.path.join(subj_phys, os.path.basename(phys_file))
        dest_new = os.path.join(
            subj_phys,
            f"sub-{subid}_{sess}_{task}_{run}_recording-biopack_physio.acq",
        )

        # Copy, rename
        shutil.copy(phys_file, dest_orig)
        os.rename(dest_orig, dest_new)


# %%
def dcm_worflow(
    subid, dcm_list, raw_path, deriv_dir, do_deface, beh_list, phys_list
):
    """Conduct DICOM conversion worklow.

    Coordinate resources for MRI conversion, BIDSification,
    generating events sidecars, and moving physio data.

    Parameters
    ----------
    subid
    dcm_list : list
        Paths to sourcedata DICOM directories
    raw_path : path
        Location of subject's rawdata
    deriv_dir : path
        Location of derivatives directory
    do_deface : bool
        Whether to deface T1w files
    beh_list : list
        Paths to task csv files
    phys_list : list
        Acq files

    Returns
    -------
    None

    """
    print(f"\nProcessing data for {subid} ...")
    _process_mri(dcm_list, raw_path, deriv_dir, subid, do_deface)
    _process_beh(beh_list, raw_path, subid)
    _process_phys(phys_list, raw_path, subid)
