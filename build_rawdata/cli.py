r"""Convert DICOMs to NIfTI files.

Converts all DICOMs in a subject's session
sourcedata DICOM directory into BIDS-formatted
NIfTI files, output to rawdata.

Notes
-----
Requires EmoRep_BIDS sourcedata organization.

Examples
--------
build_rawdata --sub-all --deface

build_rawdata \
    --sub-list ER0009 ER0016 \
    --raw-dir /path/to/project/bids/rawdata \
    --deface

"""
# %%
import os
import sys
import glob
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter
from build_rawdata import workflow
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
        help=textwrap.dedent(
            """\
            Whether to deface via pydeface,
            True if "--deface" else False.
            """
        ),
    )
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
        help=textwrap.dedent(
            """\
            Whether to process all participant data in <proj_dir>/sourcedata,
            True if "--sub-all" else False.
            """
        ),
    )
    parser.add_argument(
        "--sub-list",
        nargs="+",
        help=textwrap.dedent(
            """\
            List of subject IDs to submit for pre-processing,
            e.g. "--sub-list ER4414" or "--sub-list ER4414 ER4415 ER4416".
            """
        ),
        type=str,
    )

    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return parser


# %%
def main():
    """Coordinate module resources."""
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
    wf = workflow.ConvertSourcedata(
        source_path, raw_path, deriv_dir, do_deface
    )
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
