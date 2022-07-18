"""Deface T1w NIfTI files.

Notes
-----
Requires pydeface.
"""
import os
import subprocess
from pathlib import Path


def deface(t1_list, deriv_dir, subid, sess):
    """Deface T1w files.

    Submits a bash subprocess that calls Poldrack's pydeface.

    Parameters
    ----------
    t1_list : list
        Paths to subject T1w niis in rawdata
    deriv_dir : Path
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
