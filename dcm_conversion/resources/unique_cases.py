"""Methods for resolving data issues.

Inevitably some participants will have idiosyncratic data,
or a protocol will change, resulting in special cases that
need to be treated specially by the package.

"""


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
    bold_lists : list
        List of lists, where each sub-list contains the bold
        images to be associated with a given fmap file.

    """

    subs_to_tend = {
        "ER0909": {
            "ses-day2": {
                "fmap1": [
                    "scenarios_01",
                    "scenarios_02",
                    "scenarios_03",
                    "scenarios_04",
                    "scenarios_05",
                ],
                "fmap2": [
                    "scenarios_07",
                    "scenarios_08",
                    "rest_01",
                ],
            },
            "ses-day3": {
                "fmap1": [
                    "scenarios_01",
                    "scenarios_02",
                    "scenarios_03",
                    "scenarios_04",
                ],
                "fmap2": [
                    "scenarios_05",
                    "scenarios_06",
                    "scenarios_07",
                    "scenarios_08",
                    "rest_01",
                ],
            },
        },
    }

    if subid in subs_to_tend.keys():
        # For each fmap, create a list of bold file names
        # that matches the list of keys.
        bold_lists = []
        for fmap in sorted(subs_to_tend[subid][sess].keys()):
            this_list = []
            for bold_key in subs_to_tend[subid][sess][fmap]:
                task, run = bold_key.split("_")
                for bold_file in bold_list:
                    if (f"task-{task}" in bold_file) and (
                        f"run-{run}" in bold_file
                    ):
                        this_list.append(bold_file)
            bold_lists.append(this_list)

    else:
        bold_lists = None

    return bold_lists
