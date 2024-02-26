"""Convert DICOMs to NIfTI files.

Use Chris Rorden's dcm2niix to convert DICOMs to NIfTI files. Also rename
files and restructure directory organizaton for BIDS compliance. Finally,
deface via AFNI's refacer.

error_msg : write out standardized error messages
dcm2niix : trigger dcm2niix for DICOM dir
deface : conduct deface of T1w files

Notes
-----
Assumes flat DICOM organization.
Assumes T1w exist for each session.

"""

import os
import shutil
import glob
import subprocess
import textwrap
import pydeface  # noqa: F401


def error_msg(msg: str, stdout: str, stderr: str):
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


def dcm2niix(subj_source, subj_raw, subid, sess):
    """Conduct dcm2niix.

    Convert all DICOMs existing in subj_source and write
    out to subj_raw.

    Parameters
    ----------
    subj_source : str, os.PathLike
        Subject's DICOM directory in sourcedata
    subj_raw : str, os.PathLike
        Subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string

    Returns
    -------
    tuple
        [0] = list of paths to niis
        [1] = list of paths to jsons

    Notes
    -----
    Writes dcm2niix-named NIfTI files to subject's rawdata.

    Raises
    ------
    FileNotFoundError
        If NIFTI files are not dected in subject rawdata.
        If the number of NIfTI and JSON are != in subject rawdata.

    """
    # Check for previous work
    nii_list = sorted(glob.glob(f"{subj_raw}/*.nii.gz"))
    if nii_list:
        json_list = sorted(glob.glob(f"{subj_raw}/*.json"))
        return (nii_list, json_list)

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

    # Clean localizers, check that dcm2niix worked
    for rm_file in glob.glob(f"{subj_raw}/DICOM_localizer*"):
        os.remove(rm_file)
    nii_list = sorted(glob.glob(f"{subj_raw}/*.nii.gz"))
    json_list = sorted(glob.glob(f"{subj_raw}/*.json"))
    if not nii_list:
        error_msg(
            "dcm2niix failed!",
            job_out.decode("utf-8"),
            job_err.decode("utf-8"),
        )
        raise FileNotFoundError("No NIfTI files detected.")
    elif len(nii_list) != len(json_list):
        raise FileNotFoundError("Unbalanced number of NIfTI and JSON files.")
    return (nii_list, json_list)


def deface(t1_list, deriv_dir, subid, sess):
    """Deface T1w files via AFNI's refacer.

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
    Writes defaced file to subject's derivatives/deface

    Returns
    -------
    list
        Location of defaced T1w file

    Raises
    ------
    FileNotFoundError
        If defaced file not detected

    """
    # Setup subject deface derivatives dir
    subj_deriv = os.path.join(deriv_dir, "deface", f"sub-{subid}", sess)
    if not os.path.exists(subj_deriv):
        os.makedirs(subj_deriv)

    deface_list = []
    for t1_path in t1_list:

        # Determine input, outut paths and name
        t1_file = os.path.basename(t1_path)
        t1_deface = os.path.join(
            subj_deriv, t1_file.replace("T1w.nii.gz", "T1w_defaced.nii.gz")
        )

        # Avoid repeating work
        if os.path.exists(t1_deface):
            deface_list.append(t1_deface)
            continue
        print(f"\t\tDefacing T1w for sub-{subid}, {sess} ...")

        # Create intermediary directory, split path for cleaning
        reface_deriv = os.path.join(deriv_dir, "reface")
        subj_reface_deriv = os.path.join(reface_deriv, f"sub-{subid}", sess)
        if not os.path.exists(subj_reface_deriv):
            os.makedirs(subj_reface_deriv)

        # Run afni refacer to deface t1w
        reface_output = os.path.join(subj_reface_deriv, "refaced.nii.gz")
        bash_reface_cmd = f"""\
            @afni_refacer_run \
            -input {t1_path} \
            -mode_deface \
            -prefix {reface_output}
        """
        h_sp = subprocess.Popen(
            bash_reface_cmd, shell=True, stdout=subprocess.PIPE
        )
        job_out, job_err = h_sp.communicate()
        h_sp.wait()

        # Check, move refaced file to deface location
        if not os.path.exists(reface_output):
            raise FileNotFoundError(
                f"Afni_refacer_run failed for {subid} {sess}."
            )
        shutil.copy(reface_output, t1_deface)

        # Cleaning up
        shutil.rmtree(reface_deriv)
        deface_list.append(t1_deface)

    return deface_list
