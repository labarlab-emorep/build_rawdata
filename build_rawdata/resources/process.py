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

import shutil
import glob
import subprocess
import textwrap
import pydeface  # noqa: F401
from build_rawdata.resources import unique_cases


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
    subj_source : path
        Subject's DICOM directory in sourcedata
    subj_raw : path
        Subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS-formatted session string

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
        return

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
        print(f"\t\t\tDefacing T1w for sub-{subid}, {sess} ...")

        # Determine input, outut paths and name
        t1_file = os.path.basename(t1_path)
        t1_deface = os.path.join(
            subj_deriv, t1_file.replace("T1w.nii.gz", "T1w_defaced.nii.gz")
        )

        # Avoid repeating work
        # if os.path.exists(t1_deface):
        #     # REMOVE THIS FOR MAIN BRANCH
        #     os.remove(t1_deface)
        # continue

        # deface_input, clean_reorient = unique_cases.deface_issue(
        #     t1_path, deriv_dir, subid, sess
        # )
        # deface_issue will return a path

        # reface work-around
        reface_output, reface_done = unique_cases.reface_workaround(
            t1_path, deriv_dir, subid, sess, subj_deriv, t1_deface
        )

        if reface_done:
            shutil.copy(reface_output, t1_deface)
            deface_list.append(reface_output)
            return deface_list

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
        deface_list.append(t1_deface)

        # cleaning up
        # if clean_reorient:
        #     shutil.rmtree(os.path.dirname(deface_input))

    return deface_list
