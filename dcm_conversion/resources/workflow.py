"""Coordinate modules into workflow."""
import os
import re
import glob
import shutil
import subprocess as sp
import bioread  # left here for generatings requirements files
import neurokit2 as nk
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

        # Check for existing niis
        t1_list = sorted(glob.glob(f"{subj_raw}/anat/*T1w.nii.gz"))
        if not t1_list:

            # Organize DICOMs, check
            print(f"\t Organizing DICOMs for sub-{subid}, {sess} ...")
            sh_run = sp.Popen(
                f"org_dcms.sh -d {subj_source}",
                shell=True,
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            sh_out, sh_err = sh_run.communicate()
            sh_run.wait()
            check_dir = os.path.join(subj_source, "EmoRep_anat")
            if not os.path.exists(check_dir):
                print(sh_out, sh_err)
                raise FileNotFoundError(
                    "Missing expected output of bin/org_dcms.sh"
                )

            # Run dcm2niix, bidsify
            print(f"\t Converting DICOMs for sub-{subid}, {sess} ...")
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
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        out_file = os.path.join(
            subj_raw, f"sub-{subid}_{sess}_{task}_{run}_events.tsv"
        )
        if not os.path.exists(out_file):
            print(f"\t Making events file for {task}, {run} ...")
            _, _ = behavior.events(task_file, subj_raw, subid, sess, task, run)


# %%
def _process_rate(rate_list, raw_path, subid):
    """Make rest rating files for subject.

    Parameters
    ----------
    rate_list : list
        Paths to rest rating csv files
    raw_path : path
        Location of subject's rawdata directory
    subid : str
        Subject identifier

    Returns
    -------
    None

    Raises
    ------
    FileExistsError
        When more thatn 2 rating files exist
    FileNotFoundError
        When sourcedata file is missing

    """
    # Check input
    if len(rate_list) > 2:
        raise FileExistsError(
            f"Expected two rest rating files, found :\n\t{rate_list}"
        )

    # Determine session
    for rate_path in rate_list:
        if not os.path.exists(rate_path):
            raise FileNotFoundError(f"Could not find file : {rate_path}")
        rate_file = os.path.basename(rate_path)
        sess = "ses-" + rate_file.split("ses-")[1].split("_")[0]

        # Determine, setup rawdata path
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/beh")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)

        # Make rawdata file
        out_file = os.path.join(
            subj_raw, f"sub-{subid}_{sess}_rest-ratings.tsv"
        )
        if not os.path.exists(out_file):
            print(f"\t Making resting rate file for {sess} ...")
            _ = behavior.rest_ratings(rate_path, subj_raw, subid, sess)


# %%
def _process_phys(phys_list, raw_path, subid):
    """Copy physio files.

    Rename physio files to BIDS convention, organize them
    within subject session directories. Generate a tsv with
    txt extension for Autonomate.

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
    for phys_file in phys_list:

        # Get session, task strings
        sess_task = "ses-day" + phys_file.split("day")[1].split("/")[0]
        sess, h_task = _split(sess_task, subid)
        if not sess:
            continue

        # Get run, deal with resting task
        if "run" in phys_file:
            run = "run-0" + phys_file.split("_run")[1].split(".")[0]
            task = h_task
        else:
            run = "run-01"
            task = "task-rest"

        # Setup output dir/name
        subj_phys = os.path.join(raw_path, f"sub-{subid}/{sess}/phys")
        if not os.path.exists(subj_phys):
            os.makedirs(subj_phys)
        dest_orig = os.path.join(subj_phys, os.path.basename(phys_file))
        dest_acq = os.path.join(
            subj_phys,
            f"sub-{subid}_{sess}_{task}_{run}_recording-biopack_physio.acq",
        )

        # Generate tsv dataframe and copy data
        if not os.path.exists(dest_acq):
            print(f"\t Converting {sess} physio data : {task} {run}")
            try:
                df_phys, _ = nk.read_acqknowledge(phys_file)
                df_phys.to_csv(
                    re.sub(".acq$", ".txt", dest_acq),
                    header=False,
                    index=False,
                    sep="\t",
                )
                shutil.copy(phys_file, dest_orig)
                os.rename(dest_orig, dest_acq)
            except:
                # nk throws the stupid struct.error, hence the naked catch.
                "\t\t Insufficient data, continuing ..."
                continue


# %%
def dcm_worflow(
    subid,
    dcm_list,
    raw_path,
    deriv_dir,
    do_deface,
    beh_list,
    phys_list,
    rate_list,
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
        Paths to acq files
    rate_list : list
        Paths to rest ratings csv files

    Returns
    -------
    None

    """
    print(f"\nProcessing data for {subid} ...")
    _process_mri(dcm_list, raw_path, deriv_dir, subid, do_deface)
    _process_beh(beh_list, raw_path, subid)
    _process_rate(rate_list, raw_path, subid)
    _process_phys(phys_list, raw_path, subid)
    print(f"\t Done processing data for {subid}.")
