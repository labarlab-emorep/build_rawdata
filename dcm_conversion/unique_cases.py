"""Title."""


def wash_issue(trial_types, task, subid):
    """Title.

    Desc.
    """

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

    wash_update = {
        "task-movies": ["WashStimOnset", "movieblockEnd"],
        "task-scenarios": ["WashStimOnset", "textblockEnd"],
    }

    if subid in issue_list:
        trial_types["wash"] = wash_update[task]
    return trial_types
