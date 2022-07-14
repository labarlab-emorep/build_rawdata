"""Convert DICOMs to NIfTI files.

BIDs org, deface ...

Example
-------

"""
import os
import sys
import textwrap
from pathlib import Path
from argparse import ArgumentParser, RawTextHelpFormatter
from dcm_conversion import convert


def get_args():
    """Get and parse arguments."""
    parser = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--source-dir",
        default=os.path.join(
            Path(__file__).parents[3],
            "sourcedata",
        ),
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
        default=os.path.join(Path(__file__).parents[3], "rawdata"),
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

    # sess =
    print(
        f"""
        \n Argument test:\n
            source_path     : {source_path}
            raw_path        : {raw_path}
            subj_list       : {subj_list}
        """
    )


if __name__ == "__main__":
    main()
