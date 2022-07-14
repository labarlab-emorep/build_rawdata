r"""Convert DICOMs to NIfTI files.

BIDs org, deface ...

Example
-------
python cli.py \
    --subj-list ER0009 \
    --raw-dir /mnt/keoki/experiments2/EmoRep/Emorep_BIDS/test
"""
import os
import sys
import glob
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter
from dcm_conversion import convert


def get_args():
    """Get and parse arguments."""
    parser = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--source-dir",
        default="/mnt/keoki/experiments2/EmoRep/Emorep_BIDS/sourecedata",
        help=textwrap.dedent(
            """\
            Path to DICOM parent directory "sourcedata"
            (default : %(default)s)
            """
        ),
        type=str,
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
        "--sub-list",
        default=None,
        nargs="+",
        help=textwrap.dedent(
            """\
            List of subject IDs to submit for pre-processing,
            e.g. "--sub-list EM4414" or "--sub-list EM4414 EM4415 EM4416".
            (default : %(default)s)
            """
        ),
        type=str,
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser


def main():
    """Title."""
    args = get_args().parse_args()
    source_path = args.source_dir
    raw_path = args.raw_dir
    subj_list = args.subj_list

    assert len(subj_list) == 1, "Only accepting one subject atm."
    for subj in subj_list:
        dcm_list = glob.glob(f"{source_path}/{subj}/*day*/DICOM")
        for subj_source in dcm_list:
            sess_task = "ses-day" + subj_source.split("day")[1].split("/")[0]
            sess, task = sess_task.split("_")
            subj_raw = os.path.join(raw_path, f"sub-{subj}/{sess}")
            convert.dcm2niix(subj_source, subj_raw, subj, sess, task)


if __name__ == "__main__":
    main()
