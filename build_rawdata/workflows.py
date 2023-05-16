"""Coordinate modules into workflow.

BuildEmoRep : Build rawdata for Exp2_Compute_Emotion
build_nki   : Get NKI Rockland Archival data for Exp3_Classify_Archival

"""
# %%
import os
import glob
import subprocess
import boto3  # noqa: F401
from fnmatch import fnmatch
from build_rawdata.resources import emorep


# %%
class BuildEmoRep:
    """Conduct DICOM conversion worklow.

    Coordinate resources for MRI conversion, BIDSification,
    generating events sidecars, and moving physio data.
    Validate organization of sourcedata.

    Methods
    -------
    chk_sourcedata(subid)
        Check for basic organization of subject sourcedata
    convert_mri()
        Convert MRI sourcedata to BIDS-formatted rawdata
    convert_beh()
        Make BIDS events sidecars
    convert_rate()
        Process post resting state endorsements
    convert_phys()
        Copy and make txt from acq file

    Example
    -------
    build_emo = BuildEmoRep(
        "/path/to/sourcedata",
        "/path/to/rawdata",
        "/path/to/derivatives",
        True,
    )
    build_emo.chk_sourcedata("ER0909")
    build_emo.convert_mri()
    build_emo.convert_beh()
    build_emo.convert_phys()
    build_emo.convert_rate()

    Notes
    -----
    Order is important, chk_sourcedata() needs to be executed first and
    convert_mri() needs to be executed second.

    """

    def __init__(self, source_path, raw_path, deriv_dir, do_deface):
        """Initialize.

        Parameters
        ----------
        source_path : path
            Location of project sourcedata
        raw_path : path
            Location of project rawdata
        deriv_dir : path
            Location of project derivatives
        do_deface : bool
            Whether to deface T1w files

        """
        print("Initializing BuildEmoRep")
        self._source_path = source_path
        self._raw_path = raw_path
        self._deriv_dir = deriv_dir
        self._do_deface = do_deface

    def chk_sourcedata(self, subid):
        """Validate sourcedata organization.

        Parameters
        ----------
        subid : str
            Subject identifier in sourcedata

        Returns
        -------
        bool
            If basic check passed

        """
        print("\tChecking sourcedata session names ...")
        self._subid = subid

        # Check for session data
        subj_source = os.path.join(self._source_path, subid)
        sess_list = [x for x in os.listdir(subj_source) if fnmatch(x, "day*")]
        if not sess_list:
            print(
                "\tNo sourcedata properly named session directories "
                + "detected, skipping."
            )
            return False

        # Check naming of session data
        for sess in sess_list:
            try:
                day, task = sess.split("_")
            except ValueError:
                print(
                    "\tERROR: Incorrect sourcedata session directory "
                    + f"name : {sess}"
                )
                return False
            if len(day) != 4 or not (task == "movies" or task == "scenarios"):
                print(
                    "\tERROR: Incorrect sourcedata session directory "
                    + f"name : {sess}"
                )
                return False
        return True

    def convert_mri(self):
        """Trigger conversion of MRI data."""
        dcm_list = sorted(
            glob.glob(f"{self._source_path}/{self._subid}/day*/DICOM")
        )
        if not dcm_list:
            print(
                "\tNo properly organized DICOMs detected for "
                + f"sub-{self._subid}. Skipping."
            )
            return

        # Process MRI data
        mk_mri = emorep.ProcessMri(self._subid, self._raw_path)
        for dcm_source in dcm_list:
            chk_dcm = glob.glob(f"{dcm_source}/**/*.dcm", recursive=True)
            if not chk_dcm:
                print(f"\tNo DICOMs found at {dcm_source}, skipping ...")
                continue

            # Make NIfTI, bidsify, and deface
            mk_mri.make_niftis(dcm_source)
            mk_mri.bidsify_niftis()
            if self._do_deface:
                mk_mri.deface_anat(self._deriv_dir)

    def convert_beh(self):
        """Trigger conversion of behavioral data."""
        beh_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*"
                + "/Scanner_behav/*run*csv"
            )
        )
        if not beh_list:
            print(
                "\tNo properly organized task files detected for "
                + f"sub-{self._subid}. Skipping."
            )
            return

        # Deal with update to resting state name
        beh_list = [x for x in beh_list if "Rest" not in x]
        mk_beh = emorep.ProcessBeh(self._subid, self._raw_path)
        for task_path in beh_list:
            mk_beh.make_events(task_path)

    def convert_rate(self):
        """Trigger conversion of post-rest endorsement ratings."""
        rate_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*/"
                + "Scanner_behav/*RestRating*csv"
            )
        )
        if not rate_list:
            print(
                "\tNo properly organized rest rating files detected for "
                + f"sub-{self._subid}, skipping."
            )
            return
        elif len(rate_list) > 2:
            print(
                f"\tExpected two rest rating files, found :\n\t{rate_list},"
                + " skipping"
            )
            return

        # Convert all rest ratings
        mk_rate = emorep.ProcessRate(self._subid, self._raw_path)
        for rate_path in rate_list:
            mk_rate.make_rate(rate_path)

    def convert_phys(self):
        """Trigger conversion of physiology data."""
        phys_dirs = sorted(
            glob.glob(f"{self._source_path}/{self._subid}/day*/Scanner_physio")
        )
        if not phys_dirs:
            print(
                f"\tNo physio files detected for sub-{self._subid}, skipping."
            )
            return

        # Convert all physio files
        phys_list = sorted(
            glob.glob(
                f"{self._source_path}/{self._subid}/day*/Scanner_physio/*acq"
            )
        )
        if not phys_list:
            print(
                "\tNo properly organized physio files detected for "
                + f"sub-{self._subid}, skipping."
            )
            return
        mk_phys = emorep.ProcessPhys(
            self._subid, self._raw_path, self._deriv_dir
        )
        for phys_path in phys_list:
            mk_phys.make_physio(phys_path)


# %%
def build_nki(
    age,
    dryrun,
    hand,
    nki_dir,
    proj_dir,
    prot,
    scan,
    sess,
):
    """Pull data from the NKI Rockland Archive.

    This method is really just a wrapper for the download script available at:
        http://fcon_1000.projects.nitrc.org/indi/enhanced/neurodata.html

    Setup a rawdata directory consisting of NKI Rockland Archival data,
    then clean up directory by removing physio data, adding BIDS run field,
    and shortening the subject ID (to resolve FSL buffer overlow issue).
    Data will be organized in:
        <proj_dir>/data_mri_BIDS/rawdata

    Parameters
    ----------
    age : int
        Age lower threshold
    dryrun : bool
        Test the download parameters
    hand : str
        Handedness of participants
    nki_dir : str, os.PathLike
        Location of directory containing NKI files:
        -   aws_links.csv
        -   download_rockland_raw_bids_ver2.py
    proj_dir : str, os.PathLike
        Parent directory of project
    port : str
        Scanning protocol
    scan : list
        Scan types to download
    sess : str
        Session, Visit name

    Raises
    ------
    FileNotFoundError
        Missing required files
    ValueError
        Unexpected values for parameters

    """
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

    # Check for required files, setup
    pull_script = os.path.join(nki_dir, "download_rockland_raw_bids_ver2.py")
    pull_link = os.path.join(nki_dir, "aws_links.csv")
    for _chk in [pull_script, pull_link]:
        if not os.path.exists(_chk):
            raise FileNotFoundError(f"Expected file : {_chk}")
    raw_path = os.path.join(proj_dir, "data_mri_BIDS", "rawdata")
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)

    # Build pull command, execute
    pull_list = [
        "python",
        pull_script,
        f"-al {pull_link}",
        f"-o {raw_path}",
        f"-v {sess}",
        f"-e {prot}",
        f"-t {' '.join(scan)}",
        f"-gt {age}",
    ]
    if dryrun:
        pull_list.append("-n")
    if hand:
        pull_list.append(f"-m {hand}")

    pull_cmd = " ".join(pull_list)
    print(f"Running pull command :\n\t{pull_cmd}\n")
    subprocess.run(pull_cmd, shell=True)

    # Add run field to func for consistency with Exp2
    rest_all = [
        x
        for x in glob.glob(
            f"{raw_path}/**/ses-BAS1/func/*task-rest*", recursive=True
        )
        if "run-01" not in x
    ]
    for rest_path in rest_all:
        out_name = os.path.basename(rest_path).replace(
            "task-rest", "task-rest_run-01"
        )
        out_path = os.path.join(os.path.dirname(rest_path), out_name)
        if os.path.exists(out_path):
            continue
        os.replace(rest_path, out_path)

    # Remove physio
    if dryrun:
        return
    print("Removing physio files ...")
    phys_all = glob.glob(f"{raw_path}/**/*_physio.*", recursive=True)
    if phys_all:
        for phys_path in phys_all:
            os.remove(phys_path)

    # Shorten IDs
    subj_all = [
        os.path.basename(x) for x in sorted(glob.glob(f"{raw_path}/sub-*"))
    ]
    subj_switch = {x: f"sub-{x[-5:]}" for x in subj_all}
    for _long, _short in subj_switch.items():

        # Rename parent dir
        short_dir = os.path.join(raw_path, _short)
        os.rename(os.path.join(raw_path, _long), short_dir)

        # Rename files
        file_list = glob.glob(f"{short_dir}/**/{_long}_*", recursive=True)
        for _file in file_list:
            file_path, suff = _file.split(_long)
            os.rename(_file, f"{file_path}{_short}{suff}")


# %%
