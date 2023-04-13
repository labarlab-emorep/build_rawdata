"""Title.

Desc: TODO

Examples
--------
build_nki -t anat func
build_nki -t anat func --hand R --dryrun

"""
# %%
import os
import sys
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter
from build_rawdata import workflows
import build_rawdata._version as ver


# %%
def get_args():
    """Get and parse arguments."""
    ver_info = f"\nVersion : {ver.__version__}\n\n"
    parser = ArgumentParser(
        description=ver_info + __doc__, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--age",
        default=17,
        help=textwrap.dedent(
            """\
            Threshold age, will pull data for participants
            of older (>) than specified age.
            (default : %(default)s)
            """
        ),
        type=int,
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="Test download parameters"
    )
    parser.add_argument(
        "--hand",
        help=textwrap.dedent(
            """\
            ["L", "R"]
            Handedness of participants, unspecified pulls both
            """
        ),
        type=int,
    )
    parser.add_argument(
        "--nki-dir",
        default="/mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival/code/nki_resources",  # noqa: E501
        help=textwrap.dedent(
            """\
            Path to parent directory containing download script and AWS links
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--proj-dir",
        default="/mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival",
        help=textwrap.dedent(
            """\
            Path to parent directory of archival study
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--protocol",
        default="REST1400",
        help=textwrap.dedent(
            """\
            ["REST645", "REST1400", "RESTCAP", "RESTPCASL"]
            Resting protocol name
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--session",
        default="BAS1",
        help=textwrap.dedent(
            """\
            ["BAS1", "BAS2", "BAS3"]
            Session, Visit name
            (default : %(default)s)
            """
        ),
        type=str,
    )

    required_args = parser.add_argument_group("Required Arguments")
    required_args.add_argument(
        "-t",
        "--scan-type",
        nargs="+",
        help=textwrap.dedent(
            """\
            ["anat", "func", "dwi"]
            Scan type(s) to download
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
    args = get_args().parse_args()
    age = args.age
    dryrun = args.dryrun
    hand = args.hand
    nki_dir = args.nki_dir
    proj_dir = args.proj_dir
    prot = args.protocol
    scan = args.scan_type
    sess = args.session

    # Find, check for required paths/files
    pull_script = os.path.join(nki_dir, "download_rockland_raw_bids_ver2.py")
    pull_link = os.path.join(nki_dir, "aws_links.csv")
    for _chk in [proj_dir, nki_dir, pull_script, pull_link]:
        if not os.path.exists(_chk):
            raise FileNotFoundError(
                f"Missing expected directory or file : {_chk}"
            )

    # Validate user input
    if hand:
        if hand not in ["L", "R"]:
            raise ValueError("Unexepected parameter for --hand")
    if sess not in ["BAS1", "BAS2", "BAS3"]:
        raise ValueError("Unexepected parameter for --session")
    if prot not in ["REST645", "REST1400", "RESTCAP", "RESTPCASL"]:
        raise ValueError("Unexepected parameter for --protocol")
    for _chk in scan:
        if _chk not in ["anat", "func", "dwi"]:
            raise ValueError("Unexepected parameter for --scan-type")

    workflows.build_nki(
        age,
        dryrun,
        hand,
        nki_dir,
        proj_dir,
        prot,
        pull_link,
        pull_script,
        scan,
        sess,
    )


if __name__ == "__main__":
    # Require proj env
    env_found = [x for x in sys.path if "emorep" in x]
    if not env_found:
        print("\nERROR: missing required project environment 'emorep'.")
        print("\tHint: $labar_env emorep\n")
        sys.exit(1)
    main()
