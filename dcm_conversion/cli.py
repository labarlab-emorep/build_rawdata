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
from dcm_conversion import convert, process, behavior


# %%
def _split(sess_task, subid):
    """Title.

    Desc.
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
    """Title.

    Desc.
    """
    for subj_source in dcm_list:
        sess_task = "ses-day" + subj_source.split("day")[1].split("/")[0]
        sess, task = _split(sess_task, subid)
        if not sess:
            continue

        # Setup subject rawdata, run dcm2niix
        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        print(f"\nConverting DICOMs for sub-{subid}, {sess} ...")
        nii_list, json_list = convert.dcm2niix(
            subj_source, subj_raw, subid, sess, task
        )
        t1_list = convert.bidsify(
            nii_list, json_list, subj_raw, subid, sess, task
        )
        if do_deface:
            process.deface(t1_list, deriv_dir, subid, sess)
        print("\t Done!")


# %%
def _process_beh(beh_list, raw_path, subid):
    """Title.

    Desc.
    """
    # For testing
    task_file = beh_list[0]

    for task_file in beh_list:
        sess_task = "ses-day" + task_file.split("day")[1].split("/")[0]
        sess, task = _split(sess_task, subid)
        if not sess:
            continue

        subj_raw = os.path.join(raw_path, f"sub-{subid}/{sess}")
        if not os.path.exists(subj_raw):
            os.makedirs(subj_raw)
        behavior.events(task_file, subj_raw, subid, sess, task)


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
    # For testing
    sub_list = ["ER0009"]
    raw_path = "/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/test"
    source_path = "/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/sourcedata"
    subid = sub_list[0]

    # Receive arguments
    args = get_args().parse_args()
    source_path = args.source_dir
    raw_path = args.raw_dir
    sub_list = args.sub_list
    do_deface = args.deface

    # Set derivatives location
    deriv_dir = os.path.join(os.path.dirname(raw_path), "derivatives")

    # Find each subject's source data
    for subid in sub_list:
        dcm_list = glob.glob(f"{source_path}/{subid}/day*/DICOM")
        beh_list = sorted(
            glob.glob(f"{source_path}/{subid}/day*/Scanner_behav/*run*csv")
        )

        # TODO add check for beh_list
        try:
            dcm_list[0]
        except IndexError:
            print(
                textwrap.dedent(
                    f"""
                No DICOM directory detected for {subid}'s sourcedata,
                check directory organization.
                Skipping {subid}...
                """
                )
            )
            continue

        # process mri, beh data
        _process_mri(dcm_list, raw_path, deriv_dir, subid, do_deface)
        _process_beh(beh_list, raw_path, subid)


if __name__ == "__main__":
    main()
