"""Conduct user-requested unit and integration tests.

Examples
--------
python run_tests.py --unit-all
python run_tests.py --unit-no-mark
python run_tests.py --unit-dcm-bids --unit-deface
python run_tests.py --integ-emorep

"""

import sys
import subprocess as sp
from argparse import ArgumentParser, RawTextHelpFormatter
import build_rawdata._version as ver


# %%
def get_args():
    """Get and parse arguments."""
    ver_info = f"\nVersion : {ver.__version__}\n\n"
    parser = ArgumentParser(
        description=ver_info + __doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--unit-all",
        action="store_true",
        help="Conduct all unit tests",
    )
    parser.add_argument(
        "--unit-dcm-bids",
        action="store_true",
        help="Conduct marked unit tests for DICOM to BIDs workflow",
    )
    parser.add_argument(
        "--unit-deface",
        action="store_true",
        help="Conduct marked unit tests for defacing workflow",
    )
    parser.add_argument(
        "--unit-no-mark",
        action="store_true",
        help="Conduct un-marked unit test",
    )
    parser.add_argument(
        "--integ-emorep",
        action="store_true",
        help="Conduct marked itegration tests of emorep",
    )

    if len(sys.argv) <= 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return parser


def _submit_pytest(pytest_opts: list = None):
    """Submit subprocess pytest."""
    pytest_cmd = ["python", "-m pytest", "-vv"]
    if pytest_opts:
        pytest_cmd = pytest_cmd + pytest_opts
    h_sp = sp.Popen(" ".join(pytest_cmd), shell=True)
    job_out, job_err = h_sp.communicate()
    h_sp.wait()


# %%
def main():
    """Coordinate module resources."""
    args = get_args().parse_args()

    # Unit tests
    if args.unit_all:
        _submit_pytest()
    if args.unit_no_mark:
        _submit_pytest(
            pytest_opts=["-m 'not dcm_bids and not deface and not integ'"]
        )
    if args.unit_dcm_bids:
        _submit_pytest(pytest_opts=["-m dcm_bids"])
    if args.unit_deface:
        _submit_pytest(pytest_opts=["-m deface"])

    # Integration tests
    if args.integ_emorep:
        _submit_pytest(pytest_opts=["-m integ_emorep"])


if __name__ == "__main__":
    main()
