# Importing third-party libraries
import os
import sys
import pandas as pd
import pm4py

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom src modules
from src.event_log_analyzer.simulation_parameter_extractor import get_tasks

# Time metric
def calculate_mean_cycle_time(event_log: pd.DataFrame) -> float:
    """
    Calculates the mean duration of all process instances (in minutes) in the event log
    """
    return event_log.groupby("case:concept:name")["time:timestamp"].apply(lambda x: (x.max() - x.min()).total_seconds() / 60).mean()

# Cost metric
def calculate_mean_process_costs(event_log: pd.DataFrame) -> float:
    """
    Calculates the mean costs of all process instances in the event log
    """
    if ("lifecycle:transition" in event_log.columns) and ("start" in event_log["lifecycle:transition"].unique()) and ("complete" in event_log["lifecycle:transition"].unique()):
        event_log = event_log[event_log["lifecycle:transition"] == "complete"].copy()

    return event_log.groupby("case:concept:name")["cost:amount"].sum().mean()

# Quality metric
def calculate_repeatability(event_log: pd.DataFrame) -> float:
    """
    Implements rep = 1 - (Sum[C_a] / Sum[I_a]) for the whole event log, 
    whereas C_a represents the number of unique cases in which activity 'a' 
    occurs at least once, and I_a represents the total number of occurrences 
    (instantiations) of activity 'a' across the entire event log
    """
    sum_i_a = len(event_log)

    sum_c_a = event_log.groupby("concept:name")["case:concept:name"].nunique().sum()

    return 1 - (sum_c_a / sum_i_a)

# Flexibility metric
def calculate_optionality(event_log: pd.DataFrame) -> float:
    """
    Calculates the degree of optionality as a flexibility indicator.
    The metric is defined as the ratio of optional tasks to the total number of distinct tasks.
    A task is considered optional if there exists at least one trace (variant) in the 
    log where the task does not occur
    """
    distinct_traces = pm4py.get_variants(event_log)

    distinct_tasks = get_tasks(event_log)
    number_distinct_tasks = len(distinct_tasks)

    number_optional_tasks = 0

    for task in distinct_tasks:
        for trace in distinct_traces.keys():
            if task not in trace:
                number_optional_tasks += 1
                break

    return number_optional_tasks / number_distinct_tasks