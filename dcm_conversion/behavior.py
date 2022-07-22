"""Generate events files.

Construct BIDS events sidecar and json files
for fMRI data.
"""
import os
import json
import pandas as pd
import numpy as np


# %%
class _EventsData:
    """Create BIDS events sidecar.

    Extract specified values from task csv files to construct
    BIDS events sidecars for func data.

    Written for EmoRep movies and scenarious tasks.

    Attributes
    ----------
    run_df : pd.DataFrame
        Task info from run file
    resp_na : str
        Not applicable indencator
        (default : "n/a")
    event_cols : list
        BIDS events header values (column names)
    events_df : pd.DataFrame
        Extracted BIDS events info

    """

    def __init__(self, task_file, resp_na="n/a"):
        """Read-in data and setup output dataframe.

        Parameters
        ----------
        task_file : Path
            Location of task csv file for run
        resp_na : str
            Not applicable indecator
            (default : "n/a")
        """
        self.run_df = pd.read_csv(task_file, na_values=["None", "none"])
        self.resp_na = resp_na
        self.events_cols = [
            "onset",
            "duration",
            "trial_type",
            "stim_info",
            "response",
            "response_time",
            "accuracy",
        ]

        self.events_df = pd.DataFrame(columns=self.events_cols)

    def get_info(self, event_name, event_on, event_off):
        """Mine task file for events info.

        Extact values to fill self.events_df for the columns found
        in self.events_cols. Extracts values based on input parameters.

        Parameters
        ----------
        event_name : str
            User-specified event name, for trial_type
        event_on : str
            Event onset indecator
        event_off : str
            Event offset indecator

        """
        # Get index of event onset and offset
        idx_onset = self.run_df.index[self.run_df["type"] == event_on].tolist()
        idx_offset = self.run_df.index[
            self.run_df["type"] == event_off
        ].tolist()

        # Get start/end times, calculate durations, round sig figs
        event_onset = self.run_df.loc[idx_onset, "timefromstart"].tolist()
        event_offset = self.run_df.loc[idx_offset, "timefromstart"].tolist()
        event_duration = [y - x for (x, y) in zip(event_onset, event_offset)]
        event_onset = [round(x, 2) for x in event_onset]
        event_duration = [round(x, 2) for x in event_duration]

        # Start dictionary, populate with onset, duration, and trial_type
        event_dict = dict.fromkeys(self.events_cols, "")
        event_dict["onset"] = event_onset
        event_dict["duration"] = event_duration
        event_dict["trial_type"] = np.repeat(
            event_name, len(idx_onset)
        ).tolist()

        # Setup string switch for certain events
        stim_switch = {
            "fixS": "fixation_cross",
            "fix": "fixation_cross",
            "replay": "prompt_replay",
            "judge": "prompt_in_out",
            "emotion": "select_emotion",
            "intensity": "select_intensity",
        }

        # Populate stim_info, accounting for different events
        if event_name in ["movie", "scenario", "wash"]:
            event_dict["stim_info"] = self.run_df.loc[
                idx_onset, "stimdescrip"
            ].tolist()
        elif event_name in stim_switch.keys():
            event_dict["stim_info"] = np.repeat(
                stim_switch[event_name], len(idx_onset)
            ).tolist()
        else:
            event_dict["stim_info"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()

        # Setup judge response, accuracy lists (a bit hacky)
        if event_name == "judge":
            idx_jud_resp = self.run_df.index[
                self.run_df["type"] == "JudgeResponse"
            ].tolist()
            h_jud_resp = self.run_df.loc[idx_jud_resp, "stimtype"].tolist()
            jud_resp = []
            jud_acc = []
            for h_jud in h_jud_resp:
                if pd.isna(h_jud):
                    jud_resp.append(h_jud)
                    jud_acc.append(h_jud)
                else:
                    jud_resp.append(h_jud[:1])
                    jud_acc.append(h_jud[1:])

        # Populate response & response_time, accounting for different events
        if event_name in ["emotion", "intensity"]:
            event_dict["response"] = self.run_df.loc[
                idx_offset, "stimdescrip"
            ].tolist()
            resp_time = self.run_df.loc[idx_offset, "timefromstart"].tolist()
            resp_time = [x - y for x, y in zip(resp_time, event_onset)]
            resp_time = [round(float(x), 2) for x in resp_time]
            event_dict["response_time"] = resp_time
        elif event_name == "judge":
            event_dict["response"] = jud_resp
            resp_time = self.run_df.loc[idx_jud_resp, "stimdescrip"].tolist()
            resp_time = [round(float(x), 2) for x in resp_time]
            event_dict["response_time"] = resp_time
        else:
            event_dict["response"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()
            event_dict["response_time"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()

        # Populate accuracy for judgment events
        if event_name == "judge":
            event_dict["accuracy"] = jud_acc
        else:
            event_dict["accuracy"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()

        # Convert to DataFrame, sort index by onset time
        df_event = pd.DataFrame(event_dict, columns=event_dict.keys())
        self.events_df = pd.concat(
            [self.events_df, df_event], ignore_index=True
        )
        self.events_df = self.events_df.sort_values(by=["onset"])
        self.events_df = self.events_df.reset_index(drop=True)
        del event_dict


# %%
def events(task_file, subj_raw, subid, sess, task, run):
    """Coordinate events file construction.

    Determine event names and on/offset strings for each task,
    build the events file, then write it to appropriate location.
    Finally, generate events.json files, supplying custom events
    columns and trial_type/stim_info values.

    Parameters
    ----------
    task_file : Path
        Location of task run file
    subj_raw : Path
        Location of subject's rawdata directory
    subid : str
        Subject identifier
    sess : str
        BIDS session
    task : str
        BIDS task
    run : str
        BIDS run
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

    # Determine relevant trial types, build events file
    trial_types = exp_types[task]
    events_info = _EventsData(task_file)
    for h_name, on_off in trial_types.items():
        events_info.get_info(h_name, on_off[0], on_off[1])

    # Write out events file
    out_file = os.path.join(
        subj_raw,
        f"sub-{subid}_{sess}_{task}_{run}_events.tsv",
    )
    events_info.events_df.to_csv(out_file, sep="\t", index=False, na_rep="NaN")
    del events_info

    # Prepare task info for events json
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
    event_json = f"{subj_raw}/sub-{subid}_{sess}_{task}_{run}_events.json"
    with open(event_json, "w") as jf:
        json.dump(event_dict, jf)
