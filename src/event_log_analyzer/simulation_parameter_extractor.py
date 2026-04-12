import pandas as pd

def calculate_arrival_time_statistics(event_log: pd.DataFrame) -> dict:
    """
    Calculates statistical measures (min, max, mean, var, std) regarding the case arrival time that can be used for different simulation distributions
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

def get_resources(event_log: pd.DataFrame) -> list:
    """
    Returns the names of all resources in the event log
    """
    return list(event_log["org:resource"].unique())

def get_resources_per_task(event_log: pd.DataFrame) -> dict:
    """
    Returns a dictionary with all tasks and its associated resources in the event log
    """
    return event_log.groupby("concept:name")["org:resource"].unique().to_dict()

# TODO: Method for calculating the mean time of tasks