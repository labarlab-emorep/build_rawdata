import os
import json
import pandas as pd
from pandas.testing import assert_frame_equal


def test_events_tsv(fixt_setup, fixt_behavior):
    events_tsv = fixt_behavior["events_tsv"]
    assert os.path.exists(events_tsv)
    df_test = pd.read_csv(events_tsv, sep="\t")

    events_ref = fixt_setup["ref_beh_tsv"]
    df_ref = pd.read_csv(events_ref, sep="\t")
    assert_frame_equal(df_ref, df_test)


def test_events_json(fixt_setup, fixt_behavior):
    events_json = fixt_behavior["events_json"]
    assert os.path.exists(events_json)
    with open(events_json) as ej:
        test_dict = json.load(ej)

    events_ref = fixt_setup["ref_beh_json"]
    with open(events_ref) as er:
        ref_dict = json.load(er)
    assert test_dict == ref_dict


def test_rest_ratings(fixt_rest_ratings):
    df_rest = fixt_rest_ratings["df_rest"]
    df_ref = fixt_rest_ratings["df_ref"]
    assert_frame_equal(df_rest, df_ref)
