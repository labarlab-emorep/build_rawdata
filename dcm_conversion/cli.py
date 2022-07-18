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
from dcm_conversion import convert, process


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

    # Set derivatives location
    deriv_dir = os.path.join(os.path.dirname(raw_path), "derivatives")

    # Find each subject's DICOMs
    for subid in sub_list:
        dcm_list = glob.glob(f"{source_path}/{subid}/day*/DICOM")

        # Determine session, task from path string
        for subj_source in dcm_list:
            sess_task = "ses-day" + subj_source.split("day")[1].split("/")[0]
            sess, task = sess_task.split("_")

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


if __name__ == "__main__":
    main()
