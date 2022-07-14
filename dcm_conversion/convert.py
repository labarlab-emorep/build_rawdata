"""Title.

Desc.
"""
import os
import subprocess


def dcm2niix(subj_source, subj_raw, subj, sess):
    """Title.

    Desc.
    """
    nii_name_prefix = f"sub-{subj}_ses-{sess}"

    bash_cmd = f"""\
        dcm2niix \
            -a y \
            -ba y \
            -z y \
            -o {subj_raw} \
            -i {subj_source}
    """
    h_sp = subprocess.Popen(bash_cmd, shell=True, stdout=subprocess.PIPE)
    job_out, job_err = h_sp.communicate()
    h_sp.wait()
