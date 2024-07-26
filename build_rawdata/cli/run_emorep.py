r"""Build BIDS rawdata for EmoRep experiment.

Written for for use on labarserv2.

Referencing data collected at the scanner, build a BIDS-organized
rawdata with NIfTIs, behavioral events, resting-state task response,
and physiological data. Optional defacing is available for NDAR
purposes and is written to derivatives.

Requires in-house EmoRep sourcedata organization.

Examples
--------
build_emorep --deface --sub-all
build_emorep --deface --sub-list ER0009 ER0016

"""

# %%
import os
import sys
import glob
import textwrap
import platform
from argparse import ArgumentParser, RawTextHelpFormatter
from build_rawdata import workflows
from build_rawdata.resources import bidsify
import build_rawdata._version as ver


# %%
def get_args():
    """Get and parse arguments."""
    ver_info = f"\nVersion : {ver.__version__}\n\n"
    parser = ArgumentParser(
        description=ver_info + __doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--deface",
        action="store_true",
        help="Deface anat files via @afni_refacer_run",
    ),
    parser.add_argument(
        "--proj-dir",
        default="/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS",  # noqa: E501
        help=textwrap.dedent(
            """\
            Path to BIDS organized parent directory, containing sourcedata
            and rawdata.
            (default : %(default)s)
            """
        ),
        type=str,
    )
    parser.add_argument(
        "--sub-all",
        action="store_true",
        help="Build rawdata for all participants in sourcedata",
    )
    parser.add_argument(
        "--sub-list",
        nargs="+",
        help="Subject IDs",
        type=str,
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
    proj_dir = args.proj_dir
    sub_all = args.sub_all
    sub_list = args.sub_list
    do_deface = args.deface

    raw_path = os.path.join(proj_dir, "rawdata")
    source_path = os.path.join(proj_dir, "sourcedata")

    # Set derivatives location, write project BIDS files
    print("\nMaking rawdata and derivatives BIDS compliant ...")
    deriv_dir = os.path.join(os.path.dirname(raw_path), "derivatives")
    for h_dir in [deriv_dir, raw_path]:
        if not os.path.exists(h_dir):
            os.makedirs(h_dir)
    _ = bidsify.bidsify_exp(raw_path)

    if sub_all:
        sub_list = [
            os.path.basename(x) for x in glob.glob(f"{source_path}/ER*")
        ]
        print(
            f"\nOption --sub-all envoked, processing data for:\n\t{sub_list}"
        )

    # Start workflow for each subject
    wf = workflows.BuildEmoRep(source_path, raw_path, deriv_dir, do_deface)
    for subid in sub_list:
        print(f"\nWorking on {subid}")
        chk_pass = wf.chk_sourcedata(subid)
        if not chk_pass:
            continue
        wf.convert_mri()
        wf.convert_beh()
        wf.convert_rate()
        wf.convert_phys()


if __name__ == "__main__":
    # Require proj env
    env_found = [x for x in sys.path if "emorep" in x]
    if not env_found:
        print("\nERROR: missing required project environment 'emorep'.")
        print("\tHint: $labar_env emorep\n")
        sys.exit(1)
    main()
