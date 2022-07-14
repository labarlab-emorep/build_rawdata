"""Title.

Desc.
"""
import os
import subprocess


def dcm2niix(subj_source, subj_raw, subj, sess, task):
    """Title.

    Desc.
    """
    if not os.path.exists(subj_raw):
        os.makedirs(subj_raw)

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
    return (job_out, job_err)
