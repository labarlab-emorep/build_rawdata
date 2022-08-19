"""Convert DICOMs to NIfTI files.

Use Chris Rorden's dcm2niix to convert DICOMs to NIfTI files. Also rename
files and restructure directory organizaton for BIDS compliance. Finally,
deface via pydeface.

Notes
-----
Assumes flat DICOM organization.
Assumes T1w exist for each session.
"""
import os
import glob
import subprocess
import textwrap
import pydeface  # left here for generatings requirements files


def _error_msg(msg, stdout, stderr):
    """Print stdout and stderr."""
    error_message = f"""
            {msg}

            stdout
            ------
            {stdout}

            stderr
            ------
            {stderr}
        """
    print(textwrap.dedent(error_message))


def dcm2niix(subj_source, subj_raw, subid, sess, task):
    """Conduct dcm2niix.

    Point dcm2niix at a DICOM directory, rename NIfTI
    files according to BIDs specifications, and update
    fmap json files with "IntendedFor" field.

    Parameters
    ----------
    subj_source : path
        Subject's DICOM directory in sourcedata
    subj_raw : path
        Subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string
    task : str
        BIDS-formatted task string

    Notes
    -----
    Writes dcm2niix-named NIfTI files to subject's rawdata.

    Returns
    -------
    tuple
        [0] = list of output niis
        [1] = list of output jsons

    Raises
    ------
    FileNotFoundError
        If NIFTI files are not dected in subject rawdata.
        If the number of NIfTI and JSON are != in subject rawdata.

    """
    # Construct and run dcm2niix cmd
    bash_cmd = f"""\
        dcm2niix \
            -a y \
            -ba y \
            -z y \
            -o {subj_raw} \
            {subj_source}
    """
    h_sp = subprocess.Popen(bash_cmd, shell=True, stdout=subprocess.PIPE)
    job_out, job_err = h_sp.communicate()
    h_sp.wait()

    # Clean localizers, make nii/json lists
    for rm_file in glob.glob(f"{subj_raw}/DICOM_localizer*"):
        os.remove(rm_file)
    nii_list = sorted(glob.glob(f"{subj_raw}/*.nii.gz"))
    json_list = sorted(glob.glob(f"{subj_raw}/*.json"))

    # Check that dcm2nix worked
    if job_out:
        job_out = job_out.decode("utf-8")
    if job_err:
        job_err = job_err.decode("utf-8")
    if not nii_list:
        _error_msg("dcm2niix failed!", job_out, job_err)
        raise FileNotFoundError("No nii files detected.")
    elif len(nii_list) != len(json_list):
        raise FileNotFoundError("Unbalanced json and nii lists.")

    return (nii_list, json_list)


def deface(t1_list, deriv_dir, subid, sess):
    """Deface T1w files.

    Submits a bash subprocess that calls Poldrack's pydeface.

    Parameters
    ----------
    t1_list : list
        Paths to subject T1w niis in rawdata
    deriv_dir : path
        Location of project derivatives directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string

    Notes
    -----
    Writes defaced file to subject's derivatives/deface.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If defaced file not detected.
    """
    # Setup subject deface derivatives dir
    subj_deriv = os.path.join(deriv_dir, "deface", f"sub-{subid}", sess)
    if not os.path.exists(subj_deriv):
        os.makedirs(subj_deriv)

    for t1_path in t1_list:
        print(f"\t Defacing T1w for sub-{subid}, {sess} ...")

        # Determine input, outut paths and name
        t1_file = os.path.basename(t1_path)
        t1_deface = os.path.join(
            subj_deriv, t1_file.replace("T1w.nii.gz", "T1w_defaced.nii.gz")
        )

        # Avoid repeating work
        if os.path.exists(t1_deface):
            continue

        # Write, submit defacing
        bash_cmd = f"""\
            pydeface {t1_path} --outfile {t1_deface}
        """
        h_sp = subprocess.Popen(bash_cmd, shell=True, stdout=subprocess.PIPE)
        _, _ = h_sp.communicate()
        h_sp.wait()

        # Check for output
        if not os.path.exists(t1_deface):
            raise FileNotFoundError(f"Defacing failed for {t1_path}.")
