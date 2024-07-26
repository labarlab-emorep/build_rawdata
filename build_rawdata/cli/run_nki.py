"""Download NKI Rockland Archival Data.

Download anatomical and resting-state EPI data from the
NKI Rockland Archive and setup a BIDS-organized rawdata
directory.

Essentially a project-specific wrapper for methods detailed at:
    http://fcon_1000.projects.nitrc.org/indi/enhanced/neurodata.html

The EmoRep project employed the method used in the first example,
and additional options are supplied for 'future-proofing'.

Examples
--------
build_nki -t anat func
build_nki -t anat func --hand R --dryrun
build_nki -t anat func --age 80 --dryrun
build_nki -t anat func --protocol REST645 --session BAS3 --dryrun

"""

# %%
import os
import sys
import textwrap
import platform
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
        help="Handedness of participants, unspecified pulls both",
        choices=["L", "R"],
        type=str,
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
        choices=["REST645", "REST1400", "RESTCAP", "RESTPCASL"],
        help=textwrap.dedent(
            """\
            Resting protocol name
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--session",
        default="BAS1",
        choices=["BAS1", "BAS2", "BAS3"],
        help=textwrap.dedent(
            """\
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
        choices=["anat", "func", "dwi"],
        help="Scan type(s) to download",
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
    # Check env
    if "labarserv2" not in platform.uname().node:
        print("build_rawdata is required to run on labarserv2.")
        sys.exit(1)

    # Get args
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
    for _chk in [proj_dir, nki_dir]:
        if not os.path.exists(_chk):
            raise FileNotFoundError(
                f"Missing expected directory or file : {_chk}"
            )

    workflows.build_nki(
        age,
        dryrun,
        hand,
        nki_dir,
        proj_dir,
        prot,
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
