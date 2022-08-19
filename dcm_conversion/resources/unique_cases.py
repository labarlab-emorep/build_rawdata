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
