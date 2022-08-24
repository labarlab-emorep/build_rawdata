import os
import json
import pandas as pd
from pandas.testing import assert_frame_equal


def test_events_tsv(info_behavior):
    events_tsv = info_behavior["events_tsv"]
    assert os.path.exists(events_tsv)

    events_ref = info_behavior["ref_beh_tsv"]
    df_ref = pd.read_csv(events_ref, sep="\t")
    df_test = pd.read_csv(events_tsv, sep="\t")
    assert_frame_equal(df_ref, df_test)


def test_events_json(info_behavior):
    events_json = info_behavior["events_json"]
    events_ref = info_behavior["ref_beh_json"]
    assert os.path.exists(events_json)

    with open(events_json) as ej:
        test_dict = json.load(ej)
    with open(events_ref) as er:
        ref_dict = json.load(er)
    assert test_dict == ref_dict
