import os
import json
import pandas as pd
from pandas.testing import assert_frame_equal


def test_EventsData_init(fixt_behavior):
    # Test class initializing
    assert "n/a" == fixt_behavior.ev_info._resp_na
    events_cols = [
        "onset",
        "duration",
        "trial_type",
        "stim_info",
        "response",
        "response_time",
        "accuracy",
        "emotion",
    ]
    for chk_col in events_cols:
        assert chk_col in fixt_behavior.ev_info.df_events.columns


def test_EventsData_get_info(fixt_behavior):
    # Test getting judgment info
    fixt_behavior.ev_info.get_info("judge", "JudgeOnset", "JudgeOffset")
    assert (20, 8) == fixt_behavior.ev_info.df_events.shape
    assert 22.3 == fixt_behavior.ev_info.df_events.loc[0, "onset"]
    assert 1.04 == fixt_behavior.ev_info.df_events.loc[2, "response_time"]
    assert "correct" == fixt_behavior.ev_info.df_events.loc[8, "accuracy"]

    # Test mining emotion selections
    fixt_behavior.ev_info.get_info("emotion", "EmoSelOnset", "EmoSelOffset")
    assert (24, 8) == fixt_behavior.ev_info.df_events.shape
    assert 355.15 == fixt_behavior.ev_info.df_events.loc[17, "onset"]
    assert 11.02 == fixt_behavior.ev_info.df_events.loc[17, "duration"]
    assert "emotion" == fixt_behavior.ev_info.df_events.loc[17, "trial_type"]

    # Test mining movie stim names
    fixt_behavior.ev_info.get_info("scenario", "VigOnset", "VigOffset")
    print(fixt_behavior.ev_info.df_events)
    assert (44, 8) == fixt_behavior.ev_info.df_events.shape
    assert 8.23 == fixt_behavior.ev_info.df_events.loc[0, "onset"]
    assert "excitement" == fixt_behavior.ev_info.df_events.loc[0, "emotion"]
    assert "fear" == fixt_behavior.ev_info.df_events.loc[41, "emotion"]


def test_events_json(fixt_setup, fixt_behavior):
    # Test json naming
    json_path = fixt_behavior.event_json
    subj, sess, task, run, suff = os.path.basename(json_path).split("_")
    assert fixt_setup.subj == subj
    assert fixt_setup.sess == sess
    assert fixt_setup.task == task
    assert fixt_setup.run == run
    assert "events.json" == suff

    # Test select json contents
    with open(json_path) as jf:
        event_dict = json.load(jf)
    assert (
        "A colored masking image" == event_dict["trial_type"]["Levels"]["wash"]
    )
    assert (
        "Fixation Cross" == event_dict["stim_info"]["Levels"]["fixation_cross"]
    )
    assert (
        "Emotion selected from list"
        == event_dict["response"]["Levels"]["alpha"]
    )
    assert (
        "Vignette of emotional event"
        == event_dict["trial_type"]["Levels"]["scenario"]
    )


def test_events_tsv(fixt_setup, fixt_behavior):
    # Test tsv naming
    tsv_path = fixt_behavior.event_tsv
    subj, sess, task, run, suff = os.path.basename(tsv_path).split("_")
    assert fixt_setup.subj == subj
    assert fixt_setup.sess == sess
    assert fixt_setup.task == task
    assert fixt_setup.run == run
    assert "events.tsv" == suff

    # Compare tsv against known value
    df_tst = pd.read_csv(tsv_path, sep="\t")
    df_ref = pd.read_csv(
        os.path.join(
            fixt_setup.proj_dir,
            "rawdata",
            fixt_setup.subj,
            fixt_setup.sess,
            "func",
            os.path.basename(tsv_path),
        ),
        sep="\t",
    )
    assert (93, 8) == df_tst.shape
    assert_frame_equal(df_ref, df_tst)


def test_rest_ratings(fixt_behavior):
    # Test dataframe
    assert (15, 3) == fixt_behavior.df_rest.shape
    ref_resp = [str(x) for x in [3, 2, 3, 2, 3, 1, 3, 2, 3, 3, 2, 4, 1, 3, 4]]
    assert ref_resp == fixt_behavior.df_rest["resp_int"].to_list()
