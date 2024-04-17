from build_rawdata.resources import unique_cases


def test_wash_issue(fixt_setup):
    # Set ref dict
    trial_types = {
        "fixS": ["isiOnset", "isiOffset"],
        "fix": ["IsiOnset", "IsiOffset"],
        "scenario": ["VigOnset", "VigOffset"],
        "judge": ["JudgeOnset", "JudgeOffset"],
        "replay": ["ReplayOnset", "ReplayOffset"],
        "emotion": ["EmoSelOnset", "EmoSelOffset"],
        "intensity": ["IntenSelOnset", "IntenSelOffset"],
        "wash": ["WashStimOnset", "WashStimOffset"],
    }

    # Test special case
    a_dict = unique_cases.wash_issue(
        trial_types, fixt_setup.task, fixt_setup.sess, fixt_setup.subjid
    )
    assert ["WashStimOnset", "textblockEnd"] == a_dict["wash"]

    # Test half patch
    b_dict = unique_cases.wash_issue(
        trial_types, "task-movies", "ses-day3", "ER0046"
    )
    assert trial_types == b_dict


def test_fmap_issue(fixt_setup):
    # Check special case validation
    assert not unique_cases.fmap_issue(
        fixt_setup.sess, fixt_setup.subjid, [""]
    )

    # Set up reference lists
    ref_list_a = [f"task-scenarios_run-0{x}" for x in range(1, 7)]
    ref_list_b = [f"task-scenarios_run-0{x}" for x in range(7, 9)]
    ref_list_b.append("task-rest_run-01")

    # Get test lists, compare output
    bold_list = [f"task-scenarios_run-0{x}" for x in range(1, 9)]
    bold_list.append("task-rest_run-01")
    tst_list = unique_cases.fmap_issue("ses-day3", "ER1006", bold_list)
    assert [ref_list_a, ref_list_b] == tst_list
