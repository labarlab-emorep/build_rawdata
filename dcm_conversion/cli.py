r"""Convert DICOMs to NIfTI files.

Converts all DICOMs in a subject's session
sourcedata DICOM directory into BIDS-formatted
NIfTI files, output to rawdata.

Notes
-----
Requires EmoRep_BIDS sourcedata organization.

Examples
--------
dcm_conversion -s ER0009 ER0010 --deface

python dcm_conversion/cli.py \
    --sub-list ER0009 \
    --raw-dir /mnt/keoki/experiments2/EmoRep/Emorep_BIDS/test \
    --deface
"""
# %%
import os
import sys
import glob
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter
from dcm_conversion import process, bidsify, behavior


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
        return (sess, task)
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
    raw_path : Path
        Location of subject's rawdata
    deriv_dir : Path
        Location of derivatives directory
    subid : str
        Subject identifier
    do_deface : bool
        Whether to deface T1w files

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
        except FileNotFoundError:
            f"No DICOMs detected for sub-{subid}, {sess}. Skipping."
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
                subj_source, subj_raw, subid, sess, task
            )
            t1_list = bidsify.bidsify_nii(
                nii_list, json_list, subj_raw, subid, sess, task
            )

        # Run defacing
        if do_deface:
            process.deface(t1_list, deriv_dir, subid, sess)
        print("\t Done!")


# %%
def _process_beh(beh_list, raw_path, subid):
    """Make events files for subject.

    Parameters
    ----------
    beh_list : list
        Paths to task csv files
    raw_path : Path
        Location of subject's rawdata directory
    subid : str
        Subject identifier
    """
    for task_file in beh_list:

        # Setup sess, task, and run strings
        try:
            run = "run-0" + task_file.split("run-")[1].split("_")[0]
        except IndexError:
            run = "run-0" + task_file.split("run")[1].split("_")[0]
        sess_task = "ses-day" + task_file.split("day")[1].split("/")[0]
        sess, h_task = _split(sess_task, subid)
        task = "task-" + h_task
        if not sess:
            continue

        # Make func events sidecars
        print(f"\t Making events file for {task}, {run} ...")
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}/func")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        behavior.events(task_file, subj_raw, subid, sess, task, run)


def get_args():
    """Get and parse arguments."""
    parser = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--deface",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether to deface via pydeface,
            True if "--deface" else False.
            """
        ),
    )
    parser.add_argument(
        "--raw-dir",
        default="/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/rawdata",
        help=textwrap.dedent(
            """\
            Path to DICOM parent directory "rawdata"
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--source-dir",
        default="/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/sourcedata",
        help=textwrap.dedent(
            """\
            Path to DICOM parent directory "sourcedata"
            (default : %(default)s)
            """
        ),
        type=str,
    )

    required_args = parser.add_argument_group("Required Arguments")
    required_args.add_argument(
        "-s",
        "--sub-list",
        nargs="+",
        help=textwrap.dedent(
            """\
            List of subject IDs to submit for pre-processing,
            e.g. "--sub-list ER4414" or "--sub-list ER4414 ER4415 ER4416".
            """
        ),
        type=str,
        required=True,
    )

    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return parser


# %%
def main():
    """Coordinate module resources."""
    # Receive arguments
    args = get_args().parse_args()
    source_path = args.source_dir
    raw_path = args.raw_dir
    sub_list = args.sub_list
    do_deface = args.deface

    # Set derivatives location, write project BIDS files
    deriv_dir = os.path.join(os.path.dirname(raw_path), "derivatives")
    for h_dir in [deriv_dir, raw_path]:
        if not os.path.exists(h_dir):
            os.makedirs(h_dir)
    bidsify.bidsify_exp(raw_path)

    # Find each subject's source data
    for subid in sub_list:
        dcm_list = glob.glob(f"{source_path}/{subid}/day*/DICOM")
        beh_list = sorted(
            glob.glob(f"{source_path}/{subid}/day*/Scanner_behav/*run*csv")
        )
        try:
            dcm_list[0]
            beh_list[0]
        except IndexError:
            print(
                textwrap.dedent(
                    f"""
                    DICOM directory or behavior.csv file NOT detected
                    in sourcedata of {subid}. Check directory organization.
                    Skipping {subid}...
                """
                )
            )
            continue

        # process mri, beh data
        print(f"\nProcessing data for {subid} ...")
        _process_mri(dcm_list, raw_path, deriv_dir, subid, do_deface)
        _process_beh(beh_list, raw_path, subid)


if __name__ == "__main__":
    main()
