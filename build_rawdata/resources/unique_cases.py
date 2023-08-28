"""Methods for resolving data issues.

Inevitably some participants will have idiosyncratic data,
or a protocol will change, resulting in special cases that
need to be treated specially by the package.

"""
import os
import shutil
import json
import subprocess
import importlib.resources as pkg_resources
from build_rawdata import reference_files


def wash_issue(trial_types, task, sess, subid):
    """Update wash trial endtime field.

    The WashStimOffset was incorrectly set for the
    first number of participants. This patch yields
    correct wash durations by changing the offset
    field for wash.

    Parameters
    ----------
    trial_types : dict
        Task trial types, onset, and offset fields
        produced by behavior.events.
    task : str
        BIDS task string
    sess : str
        BIDS session string
    subid : str
        Subject identifier

    Returns
    -------
    trial_types : dict
        Updated wash values if subid is found in the issue_list,
        otherwise returns the same trial_types as wash_issue received.

    """

    # List subjects who only need ses-day2 patched
    half_issue = ["ER0046", "ER0074", "ER0075"]

    # List all subjects who need a patch
    issue_list = [
        "ER0009",
        "ER0016",
        "ER0024",
        "ER0036",
        "ER0041",
        "ER0046",
        "ER0052",
        "ER0057",
        "ER0060",
        "ER0071",
        "ER0072",
        "ER0074",
        "ER0075",
        "ER0093",
        "ER0103",
    ]

    # Skip patch when ses-day3 for half_issue subjects
    if sess == "ses-day3" and subid in half_issue:
        return trial_types

    # Patch - update wash endtime
    wash_update = {
        "task-movies": ["WashStimOnset", "movieblockEnd"],
        "task-scenarios": ["WashStimOnset", "textblockEnd"],
    }
    if subid in issue_list:
        trial_types["wash"] = wash_update[task]
    return trial_types


def fmap_issue(sess, subid, bold_list):
    """Provide lists of func runs to associate with each fmap.

    For various reasons, certain functional runs may need to
    be paired with specific fmap acquisitions for certain participants.
    This function provides those mappings.

    Parameters
    ----------
    sess : str
        BIDS session string
    subid : str
        Subject identifier
    bold_list: list
        List of bold images

    Returns
    -------
    list, None
        List of lists, where each list[0] contains bold images
        associated with fmap1, and list[1] for fmap2.

    """
    # Get user-specified unique_fmaps.json, check for subject and session
    with pkg_resources.open_text(reference_files, "unique_fmap.json") as jf:
        subs_to_tend = json.load(jf)
    if (
        subid not in subs_to_tend.keys()
        or sess not in subs_to_tend[subid].keys()
    ):
        return None

    # Get subject, session info
    map_bold_fmap = []
    sess_dict = subs_to_tend[subid][sess]
    for fmap_key, map_list in sess_dict.items():
        # Validate user-specified unique_fmaps.json setup
        if fmap_key not in ["fmap1", "fmap2"]:
            raise KeyError(
                "Unexpected key in reference_files/unique_fmap.json:"
                + f"{subid} {sess} {fmap_key}"
            )
        try:
            task, run = map_list[0].split("_")
            if task not in ["scenarios", "movies"]:
                raise ValueError(
                    "Unexpected task in reference_files/"
                    + f"unique_fmap.json: {task}"
                )
        except ValueError:
            raise ValueError(
                "Unexpected task format in reference_files/"
                + f"unique_fmap.json: {map_list[0]}"
            )

        # For each fmap, create a list of bold file names
        # that matches the list of keys.
        match_list = []
        for bold_key in map_list:
            task, run = bold_key.split("_")
            match_bold = [
                x for x in bold_list if f"task-{task}_run-{run}" in x
            ]
            if len(match_bold) == 1:
                match_list.append(match_bold[0])
            elif len(match_bold) > 1:
                raise ValueError(
                    "Too many fmap-bold matches, check task"
                    + f" and run values: {bold_key}"
                )
        map_bold_fmap.append(match_list)
    return map_bold_fmap


def deface_issue(t1_path, deriv_dir, subid, sess):
    """Reorienting the sample due to an error in defacing."""
    # Get improper defaces and check for subject and session
    with pkg_resources.open_text(reference_files, "unique_deface.json") as jf:
        subs_to_reorient = json.load(jf)
    if subid not in subs_to_reorient.keys():
        return (t1_path, False)

    # copy file into reorient_deriv directory (built in process.deface)
    subj_reorient_deriv = os.path.join(
        deriv_dir, "reorient", f"sub-{subid}", sess
    )
    if not os.path.exists(subj_reorient_deriv):
        os.makedirs(subj_reorient_deriv)

    bash_reorient_cmd = f"""\
        3dresample \
        -orient LPI \
        -rmode NN \
        -prefix {subj_reorient_deriv}/reorient.nii.gz \
        -input {t1_path}
    """
    h_sp = subprocess.Popen(
        bash_reorient_cmd, shell=True, stdout=subprocess.PIPE
    )
    job_out, job_err = h_sp.communicate()
    h_sp.wait()
    return (os.path.join(subj_reorient_deriv, "reorient.nii.gz"), True)


def reface_workaround(t1_path, deriv_dir, subid, sess, subj_deriv, t1_deface):
    """Using Afni Reface instead of Pydeface."""
    with pkg_resources.open_text(reference_files, "unique_deface.json") as jf:
        subs_to_reorient = json.load(jf)
    if subid not in subs_to_reorient.keys():
        return (t1_path, False)

    subj_reface_deriv = os.path.join(deriv_dir, "reface", f"sub-{subid}", sess)
    if not os.path.exists(subj_reface_deriv):
        os.makedirs(subj_reface_deriv)

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
    # print(job_out, job_err)
    # Check
    if not os.path.exists(subj_deriv):
        raise FileNotFoundError("some message")

    return (reface_output, True)
