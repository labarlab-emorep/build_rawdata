r"""Convert DICOMs to NIfTI files.

Converts all DICOMs in a subject's session
sourcedata DICOM directory into BIDS-formatted
NIfTI files, output to rawdata.

Notes
-----
Requires EmoRep_BIDS sourcedata organization.

Examples
--------
dcm_conversion --sub-all --deface

python dcm_conversion/cli.py \
    --sub-list ER0009 ER0016 \
    --raw-dir /mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS/rawdata \
    --deface

"""
# %%
import os
import sys
import glob
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter
from dcm_conversion.resources import bidsify, workflow


# %%
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
        "--proj-dir",
        default="/mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS",
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
    # Receive arguments
    args = get_args().parse_args()
    proj_dir = args.proj_dir
    sub_all = args.sub_all
    sub_list = args.sub_list
    do_deface = args.deface

    raw_path = os.path.join(proj_dir, "rawdata")
    source_path = os.path.join(proj_dir, "sourcedata")

    # Set derivatives location, write project BIDS files
    deriv_dir = os.path.join(os.path.dirname(raw_path), "derivatives")
    for h_dir in [deriv_dir, raw_path]:
        if not os.path.exists(h_dir):
            os.makedirs(h_dir)
    _ = bidsify.bidsify_exp(raw_path)

    if sub_all:
        sub_list = [
            os.path.basename(x) for x in glob.glob(f"{source_path}/ER*")
        ]
        print(f"Option --sub-all envoked, processing data for:\n\t{sub_list}")

    # Find each subject's source data
    for subid in sub_list:
        dcm_list = glob.glob(f"{source_path}/{subid}/day*/DICOM")
        beh_list = sorted(
            glob.glob(f"{source_path}/{subid}/day*/Scanner_behav/*run*csv")
        )
        rate_list = sorted(
            glob.glob(
                f"{source_path}/{subid}/day*/Scanner_behav/*RestRating*csv"
            )
        )
        phys_list = sorted(
            glob.glob(f"{source_path}/{subid}/day*/Scanner_physio/*acq")
        )
        try:
            dcm_list[0]
            beh_list[0]
            phys_list[0]
            rate_list[0]
        except IndexError:
            print(
                textwrap.dedent(
                    f"""
                    DICOM directory, behavior.csv, or physio.acq file NOT
                    detected in sourcedata of {subid}. Check directory
                    organization.

                    Skipping {subid}...
                """
                )
            )
            continue

        # Start workflow
        workflow.dcm_worflow(
            subid,
            dcm_list,
            raw_path,
            deriv_dir,
            do_deface,
            beh_list,
            phys_list,
            rate_list,
        )


if __name__ == "__main__":
    main()
