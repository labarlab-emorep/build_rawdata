"""Title.

Desc.
"""
import pandas as pd
import numpy as np


# %%
class EventsData:
    """Title.

    Desc.
    """

    def __init__(self, task_file, resp_na="n/a"):
        self.run_df = pd.read_csv(task_file)
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

    def get_movie(self):
        """Title.

        Desc.
        """
        # Get index of on/offset, determine duration
        idx_onset = self.run_df.index[
            self.run_df["type"] == "MovieStimOnset"
        ].tolist()
        idx_offset = self.run_df.index[
            self.run_df["type"] == "MovieStimOffset"
        ].tolist()
        movie_onset = self.run_df.loc[idx_onset, "timefromstart"].tolist()
        movie_offset = self.run_df.loc[idx_offset, "timefromstart"].tolist()
        movie_duration = [y - x for (x, y) in zip(movie_onset, movie_offset)]

        # round sig figs
        movie_onset = [round(x, 2) for x in movie_onset]
        movie_duration = [round(x, 2) for x in movie_duration]

        # start, populate dicionary
        movie_dict = dict.fromkeys(self.events_cols, "")
        movie_dict["onset"] = movie_onset
        movie_dict["duration"] = movie_duration
        movie_dict["trial_type"] = np.repeat(
            "movie", len(movie_dict["onset"])
        ).tolist()
        movie_dict["stim_info"] = self.run_df.loc[
            idx_onset, "stimdescrip"
        ].tolist()
        movie_dict["response"] = np.repeat(
            self.resp_na, len(movie_dict["onset"])
        ).tolist()
        movie_dict["response_time"] = np.repeat(
            self.resp_na, len(movie_dict["onset"])
        ).tolist()
        movie_dict["accuracy"] = np.repeat(
            self.resp_na, len(movie_dict["onset"])
        ).tolist()
        df_movie = pd.DataFrame(movie_dict, columns=movie_dict.keys())

        # update class events
        self.events_df = pd.concat(
            [self.events_df, df_movie], ignore_index=True
        )

    def get_info(self, event_name, event_on, event_off):
        """Title.

        Desc.
        """
        # Get index of event onset and offset
        idx_onset = self.run_df.index[self.run_df["type"] == event_on].tolist()
        idx_offset = self.run_df.index[
            self.run_df["type"] == event_off
        ].tolist()
        idx_jud_resp = self.run_df.index[
            self.run_df["type"] == "JudgeResponse"
        ].tolist()

        # Get start/end times, calculate durations
        event_onset = self.run_df.loc[idx_onset, "timefromstart"].tolist()
        event_offset = self.run_df.loc[idx_offset, "timefromstart"].tolist()
        event_duration = [y - x for (x, y) in zip(event_onset, event_offset)]

        # Round sig figs
        event_onset = [round(x, 2) for x in event_onset]
        event_duration = [round(x, 2) for x in event_duration]

        # Start dictionary
        event_dict = dict.fromkeys(self.events_cols, "")

        # Populate onset, duration, and trial_type
        event_dict["onset"] = event_onset
        event_dict["duration"] = event_duration
        event_dict["trial_type"] = np.repeat(
            event_name, len(idx_onset)
        ).tolist()

        # Populate stim_info
        if event_name in ["movie", "wash"]:
            event_dict["stim_info"] = self.run_df.loc[
                idx_onset, "stimdescrip"
            ].tolist()
        else:
            event_dict["stim_info"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()

        # Populate response, response_time
        if event_name in ["emotion", "intensity"]:
            event_dict["response"] = self.run_df.loc[
                idx_offset, "stimdescrip"
            ].tolist()
            resp_time = self.run_df.loc[idx_offset, "timefromstart"].tolist()
            resp_time = [round(x, 2) for x in resp_time]
            event_dict["response_time"] = resp_time
        elif event_name == "judge":
            jud_resp = self.run_df.loc[idx_jud_resp, "stimtype"].tolist()
            event_dict["response"] = [x[:1] for x in jud_resp]
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

        # Populate accuracy
        if event_name == "judge":
            jud_resp = self.run_df.loc[idx_jud_resp, "stimtype"].tolist()
            event_dict["accuracy"] = [x[1:] for x in jud_resp]
        else:
            event_dict["accuracy"] = np.repeat(
                self.resp_na, len(idx_onset)
            ).tolist()

        # Convert to DataFrame, sort time
        df_event = pd.DataFrame(event_dict, columns=event_dict.keys())
        self.events_df = pd.concat(
            [self.events_df, df_event], ignore_index=True
        )
        self.events_df = self.events_df.sort_values(by=["onset"])
        self.events_df = self.events_df.reset_index(drop=True)


# %%
def events(task_file, subj_raw, subid, sess, task):
    """Title.

    Desc.
    """

    trial_types = {
        "fixS": ["isiOnset", "isiOffset"],
        "fix": ["IsiOnset", "IsiOffset"],
        "movie": ["MovieStimOnset", "MovieStimOffset"],
        "judge": ["JudgeOnset", "JudgeOffset"],
        "replay": ["ReplayOnset", "ReplayOffset"],
        "emotion": ["EmoSelOnset", "EmoSelOffset"],
        "intensity": ["IntenSelOnset", "IntenSelOffset"],
        "wash": ["WashStimOnset", "WashStimOffset"],
    }

    events_info = EventsData(task_file)
    for h_name, on_off in trial_types.items():
        print(h_name, on_off[0], on_off[1])
        events_info.get_info(h_name, on_off[0], on_off[1])
