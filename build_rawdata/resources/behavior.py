"""Manage in-scanner task responses.

events_tsv : generate BIDS events.tsv and events.json func sidecars
rest_ratings : aggregate, clean post-rest ratings

"""

import os
import json
import pandas as pd
import numpy as np
from typing import Union, Tuple
from build_rawdata.resources import unique_cases


# %%
class _EventsData:
    """Create BIDS events sidecar.

    Extract specified values from task csv files to construct
    BIDS events sidecars for func data.

    Parameters
    ----------
    task_file : str, os.PathLike
        Location of task csv file for run
    resp_na : str, optional
        Not applicable indicator

    Attributes
    ----------
    df_events : pd.DataFrame
        Extracted BIDS events info

    Methods
    -------
    get_info()
        Extract information for a certain event type

    Notes
    -----
    Written for EmoRep movies and scenarios tasks.

    Example
    -------
    ev_info = behavior._EventsData(*args)
    ev_info.get_info("judge", "JudgeOnset", "JudgeOffset")

    """

    def __init__(self, task_file, resp_na="n/a"):
        """Read-in data and start output dataframe."""
        self._df_run = pd.read_csv(task_file, na_values=["None", "none"])
        self._resp_na = resp_na
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
        self.df_events = pd.DataFrame(columns=events_cols)

    def _stim_info(self, event_name: str, idx_onset: list) -> Tuple:
        """Conditionally get event stimulus info."""
        # Setup string switch for certain events
        stim_switch = {
            "fixS": "fixation_cross",
            "fix": "fixation_cross",
            "replay": "prompt_replay",
            "judge": "prompt_in_out",
            "emotion": "select_emotion",
            "intensity": "select_intensity",
        }

        # Get stim_info, accounting for different events
        if event_name in stim_switch.keys():
            h_stim_info = np.repeat(
                stim_switch[event_name], len(idx_onset)
            ).tolist()
        elif event_name in ["movie", "scenario", "wash"]:
            h_stim_info = self._df_run.loc[idx_onset, "stimdescrip"].tolist()
        else:
            h_stim_info = np.repeat(self._resp_na, len(idx_onset)).tolist()

        # Split movie, scenario names to capture emotion
        if event_name in ["movie", "scenario"]:
            h_stim_emo = [x.split("_")[0] for x in h_stim_info]
        else:
            h_stim_emo = np.repeat(self._resp_na, len(h_stim_info)).tolist()

        return (h_stim_info, h_stim_emo)

    def _judge_resp(self) -> Tuple:
        """Get and parse judgment responses.

        Deals with differing captures of JudgeResponse between
        movie and scenario versions of task.

        """
        idx_jud_resp = self._df_run.index[
            self._df_run["type"] == "JudgeResponse"
        ].tolist()
        h_jud_resp = self._df_run.loc[idx_jud_resp, "stimtype"].tolist()
        jud_resp = []
        jud_acc = []
        for h_jud in h_jud_resp:
            if pd.isna(h_jud):
                jud_resp.append(h_jud)
                jud_acc.append(h_jud)
            else:
                jud_resp.append(h_jud[:1])
                jud_acc.append(h_jud[1:])

        return (idx_jud_resp, jud_resp, jud_acc)

    def _resp_time(
        self,
        event_name: str,
        event_onset: list,
        idx_onset: list,
        idx_offset: list,
    ) -> Tuple:
        """Conditionally get response, response time."""
        if event_name in ["emotion", "intensity"]:
            h_resp = self._df_run.loc[idx_offset, "stimdescrip"].tolist()
            h_resp_time = self._df_run.loc[
                idx_offset, "timefromstart"
            ].tolist()
            h_resp_time = [x - y for x, y in zip(h_resp_time, event_onset)]
            h_resp_time = [round(float(x), 2) for x in h_resp_time]
        elif event_name == "judge":
            idx_jud_resp, jud_resp, _ = self._judge_resp()
            h_resp = jud_resp
            h_resp_time = self._df_run.loc[
                idx_jud_resp, "stimdescrip"
            ].tolist()
            h_resp_time = [round(float(x), 2) for x in h_resp_time]
        else:
            h_resp = np.repeat(self._resp_na, len(idx_onset)).tolist()
            h_resp_time = np.repeat(self._resp_na, len(idx_onset)).tolist()

        return (h_resp, h_resp_time)

    def get_info(self, event_name, event_on, event_off):
        """Mine task file for events info and set df_events attr.

        Extact values to fill self.df_events for the columns found
        in events_cols. Extracts values based on input parameters.

        Parameters
        ----------
        event_name : str
            User-specified event name, for trial_type
        event_on : str
            Event onset indicator
        event_off : str
            Event offset indicator

        Notes
        -----
        Updates (appends) self.df_events with event-specific information,
        then sorts by onset time.

        """
        # Get index of event onset and offset
        idx_onset = self._df_run.index[
            self._df_run["type"] == event_on
        ].tolist()
        idx_offset = self._df_run.index[
            self._df_run["type"] == event_off
        ].tolist()

        # Get start/end times, calculate durations, round sig figs
        event_onset = self._df_run.loc[idx_onset, "timefromstart"].tolist()
        event_offset = self._df_run.loc[idx_offset, "timefromstart"].tolist()
        event_duration = [y - x for (x, y) in zip(event_onset, event_offset)]
        event_onset = [round(x, 2) for x in event_onset]
        event_duration = [round(x, 2) for x in event_duration]

        # Set trial type
        event_trial_type = np.repeat(event_name, len(idx_onset)).tolist()

        # Get stimulus info for event
        event_stim_info, event_stim_emo = self._stim_info(
            event_name, idx_onset
        )

        # Determine response and response time
        event_response, event_response_time = self._resp_time(
            event_name, event_onset, idx_onset, idx_offset
        )

        # Determine accuracy of response
        if event_name == "judge":
            _, _, event_accuracy = self._judge_resp()
        else:
            event_accuracy = np.repeat(self._resp_na, len(idx_onset)).tolist()

        # Make event dataframe
        event_dict = {
            "onset": event_onset,
            "duration": event_duration,
            "trial_type": event_trial_type,
            "stim_info": event_stim_info,
            "response": event_response,
            "response_time": event_response_time,
            "accuracy": event_accuracy,
            "emotion": event_stim_emo,
        }
        df_event = pd.DataFrame(event_dict, columns=event_dict.keys())
        del event_dict

        # Append df_events with event dataframe, sort by onset time
        self.df_events = pd.concat(
            [self.df_events, df_event], ignore_index=True
        )
        self.df_events = self.df_events.sort_values(by=["onset"])
        self.df_events = self.df_events.reset_index(drop=True)


# %%
def _events_json(
    task: str, event_tsv: Union[str, os.PathLike]
) -> Union[str, os.PathLike]:
    """Generate events.json, supplying custom columns and values."""
    event_dict = {
        "trial_type": {
            "LongName": f"Emotion Task with {task.split('-')[1]}",
            "Description": "Indicator of stimulus or reponse type",
            "Levels": {
                "fixS": "Start, end fixations",
                "fix": "Fixation cross",
                "judge": "Indoor, outdoor judgment",
                "replay": "Mentally replay stimulus",
                "emotion": "Decide which emotion describes the stimulus",
                "intensity": "Decide emotional intensity level of stimulus",
                "wash": "A colored masking image",
            },
        },
        "stim_info": {
            "LongName": "Short description of stimulus",
            "Description": "Indicator of screen prompt or stimulus presented",
            "Levels": {
                "fixation_cross": "Fixation Cross",
                "prompt_replay": "Prompt to replay stimulus",
                "prompt_in_out": "Prompt to make indoor, outdoor judgment",
                "select_emotion": "Prompt to select emotion from list",
                "select_intensity": "Prompt to specify emotion intensity",
                "file name": "File used in stimulus generation",
            },
        },
        "response": {
            "LongName": "Response made by participant",
            "Description": "Captured response of participant",
            "Levels": {
                "numeric": "Indoor/outdoor judgment or intensity rating",
                "alpha": "Emotion selected from list",
            },
        },
        "accuracy": {
            "LongName": "Accuracy of participant response",
            "Description": "Whether response was correct",
            "Levels": {
                "correct": "Response was correct",
                "wrong": "Response was incorrect",
            },
        },
        "emotion": {
            "LongName": "Emotion category of stimulus",
            "Description": "Intended emotion the movie or scenario "
            + "was designed to elicit",
        },
    }

    # Add task-specific trial_types
    if task == "task-movies":
        event_dict["trial_type"]["Levels"][
            "movie"
        ] = "Movie clip of emotional event"
    elif task == "task-scenarios":
        event_dict["trial_type"]["Levels"][
            "scenario"
        ] = "Vignette of emotional event"

    # Write event json file
    event_json = event_tsv.replace(".tsv", ".json")
    with open(event_json, "w") as jf:
        json.dump(event_dict, jf)
    return event_json


# %%
def events_tsv(task_file, subj_raw, subid, sess, task, run):
    """Coordinate events file construction.

    Determine event names and on/offset strings for each task,
    build the events file, then write it to appropriate location.

    Parameters
    ----------
    task_file : str, os.PathLike
        Location of task run file
    subj_raw : str, os.PathLike
        Location of subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS session
    task : str
        BIDS task
    run : str
        BIDS run

    Returns
    -------
    tuple
        [0] = Path to events.tsv
        [1] = Path to events.json

    """
    # Setup task-specific trial_type and on/off values
    exp_types = {
        "task-movies": {
            "fixS": ["isiOnset", "isiOffset"],
            "fix": ["IsiOnset", "IsiOffset"],
            "movie": ["MovieStimOnset", "MovieStimOffset"],
            "judge": ["JudgeOnset", "JudgeOffset"],
            "replay": ["ReplayOnset", "ReplayOffset"],
            "emotion": ["EmoSelOnset", "EmoSelOffset"],
            "intensity": ["IntenSelOnset", "IntenSelOffset"],
            "wash": ["WashStimOnset", "WashStimOffset"],
        },
        "task-scenarios": {
            "fixS": ["isiOnset", "isiOffset"],
            "fix": ["IsiOnset", "IsiOffset"],
            "scenario": ["VigOnset", "VigOffset"],
            "judge": ["JudgeOnset", "JudgeOffset"],
            "replay": ["ReplayOnset", "ReplayOffset"],
            "emotion": ["EmoSelOnset", "EmoSelOffset"],
            "intensity": ["IntenSelOnset", "IntenSelOffset"],
            "wash": ["WashStimOnset", "WashStimOffset"],
        },
    }

    # Determine relevant trial types, account for unique cases
    trial_types = exp_types[task]
    trial_types = unique_cases.wash_issue(trial_types, task, sess, subid)

    # Generate events files
    events_info = _EventsData(task_file)
    for h_name, on_off in trial_types.items():
        events_info.get_info(h_name, on_off[0], on_off[1])

    # Write out events files
    event_tsv = os.path.join(
        subj_raw,
        f"sub-{subid}_{sess}_{task}_{run}_events.tsv",
    )
    events_info.df_events.to_csv(
        event_tsv, sep="\t", index=False, na_rep="NaN"
    )
    event_json = _events_json(task, event_tsv)
    return event_tsv, event_json


# %%
def rest_ratings(rate_path, subid, sess, out_file):
    """Extract participant rest-rating responses.

    Parameters
    ----------
    rate_path : path
        Location to rest rating csv files
    subid : str
        Subject identifier
    sess : str
        BIDs-formatted session
    out_file : str
        Path, name of output file

    Returns
    -------
    tuple
        [0] = pd.DataFrame
        [1] = Location of file

    """
    # Read-in data, get stimulus and response
    df_rate = pd.read_csv(rate_path, na_values="None")
    idx_stim = df_rate.index[df_rate["type"] == "RatingOnset"].tolist()
    idx_resp = df_rate.index[df_rate["type"] == "RatingResponse"].tolist()
    rate_stim = df_rate.loc[idx_stim, "stimdescrip"].tolist()
    rate_resp = df_rate.loc[idx_resp, "stimtype"].tolist()
    rate_resp = ["88" if x != x else x for x in rate_resp]

    # Make english responses
    rate_map = {
        "1": "Not At All",
        "2": "Slightly",
        "3": "Moderately",
        "4": "Very",
        "88": "NR",
    }
    rate_alpha = [rate_map[x] for x in rate_resp]

    # Write out as dataframe
    out_dict = {
        "prompt": rate_stim,
        "resp_int": rate_resp,
        "resp_alpha": rate_alpha,
    }
    df_out = pd.DataFrame(out_dict)
    df_out = df_out.sort_values(by=["prompt"], ignore_index=True)
    df_out.to_csv(out_file, sep="\t", index=False, na_rep="NaN")
    return (df_out, out_file)
