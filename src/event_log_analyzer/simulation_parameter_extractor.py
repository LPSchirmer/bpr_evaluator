# Importing third-party libraries
import pandas as pd

def calculate_arrival_time_statistics(event_log: pd.DataFrame) -> dict:
    """
    Calculates statistical measures (min, max, mean, var, std) regarding the case arrival time (in seconds) that can be used for different simulation distributions
    """
    case_times = event_log.groupby("case:concept:name")["time:timestamp"].min().reset_index(name="start_time").sort_values("start_time")
    case_times["case_wait_time"] = case_times["start_time"].diff().dt.total_seconds()
    case_times.dropna(inplace=True)

    arrival_time_statistics = {}
    statistical_measures = ["min", "max", "mean", "var", "std"]

    for statistical_measure in statistical_measures:
        arrival_time_statistics[f"arrival_time_{statistical_measure}"] = case_times["case_wait_time"].agg(statistical_measure)

    return arrival_time_statistics

def calculate_number_of_process_instances(event_log: pd.DataFrame) -> int:
    """
    Returns the number of cases in the event log (potentially useful to decide how many simulation runs a BPMN model should go through)
    """
    return event_log["case:concept:name"].nunique()

def get_tasks(event_log: pd.DataFrame) -> list:
    """
    Returns the names of all tasks in the event log
    """
    return list(event_log["concept:name"].unique())

def get_mean_activity_duration(event_log: pd.DataFrame) -> dict:
    """
    Calculates the average duration (in seconds) of each activity in the event log. If a 'lifecycle:transition' column with both 'start' and 'complete' values is available, the service time is used. 
    Otherwise, the waiting time is assumed to be zero, meaning the entire time between two consecutive activities is treated as the activity duration.
    """
    if ("lifecycle:transition" in event_log.columns) and ("start" in event_log["lifecycle:transition"].unique()) and ("complete" in event_log["lifecycle:transition"].unique()):
        event_log = event_log.sort_values(
            ["case:concept:name", "concept:name", "time:timestamp"]
        ).copy()

        event_log["occurrence"] = (
            event_log.groupby(
                ["case:concept:name", "concept:name", "lifecycle:transition"]
            ).cumcount()
        )

        start = event_log[event_log["lifecycle:transition"] == "start"]
        end = event_log[event_log["lifecycle:transition"] == "complete"]

        merged = pd.merge(
            start,
            end,
            on=["case:concept:name", "concept:name", "occurrence"],
            suffixes=("_start", "_end"),
            how="inner",
        )

        merged["duration_seconds"] = (
            merged["time:timestamp_end"] - merged["time:timestamp_start"]
        ).dt.total_seconds()

        merged["duration_seconds"] = merged["duration_seconds"].fillna(0)

        return merged.groupby("concept:name")["duration_seconds"].mean().to_dict()
    
    elif ("lifecycle:transition" in event_log.columns) and (event_log["lifecycle:transition"].unique()[0] == "complete"):
        event_log = event_log.sort_values(
            ["case:concept:name", "time:timestamp"]
        ).copy()

        event_log["duration_seconds"] = (
            event_log["time:timestamp"] - event_log.groupby("case:concept:name")["time:timestamp"]
            .shift(1)
        ).dt.total_seconds()

        event_log["duration_seconds"] = event_log["duration_seconds"].fillna(0)

        return event_log.groupby("concept:name")["duration_seconds"].mean().to_dict()

    else:
        event_log = event_log.sort_values(
            ["case:concept:name", "time:timestamp"]
        ).copy()

        event_log["duration_seconds"] = (
            event_log.groupby("case:concept:name")["time:timestamp"]
            .shift(-1) - event_log["time:timestamp"]
        ).dt.total_seconds()

        event_log["duration_seconds"] = event_log["duration_seconds"].fillna(0)

        return event_log.groupby("concept:name")["duration_seconds"].mean().to_dict()

def get_costs_per_activity(event_log: pd.DataFrame) -> dict:
    """
    Returns the mean cost of each activity in the event log in a dict (key: activity, value: cost)
    """
    return (event_log.groupby("concept:name")
            .agg(mean_costs = ("cost:amount", "mean"))
            .to_dict()["mean_costs"])

def get_number_of_resources(event_log: pd.DataFrame) -> int:
    """
    Returns the number of unique resources in the event log
    """
    return event_log["org:resource"].nunique()