import pandas as pd
import pm4py

# Time metrics
def calculate_mean_cycle_time(event_log: pd.DataFrame) -> float:
    """
    Calculates the mean duration of a process instance (in minutes) in the event log
    """
    return event_log.groupby("case:concept:name")["time:timestamp"].apply(lambda x: (x.max() - x.min()).total_seconds() / 60).mean()

# Cost statistics
def calculate_mean_process_costs(event_log: pd.DataFrame) -> float:
    """
    Calculates the mean costs of a process instance in the event log
    """
    return event_log.groupby("case:concept:name")["cost:amount"].sum().mean()

# Quality metrics
def calculate_rework_rate(event_log: pd.DataFrame) -> float:
    """
    Calculates the rework raw by dividing the number of cases in which rework is done, through the total number of cases in the event log
    """
    number_of_rework_cases = 0

    rework_per_case = pm4py.statistics.rework.cases.pandas.get.apply(event_log)

    for value in rework_per_case.values():
        if value["rework"] != 0:
            number_of_rework_cases += 1

    return number_of_rework_cases/len(rework_per_case)

# Flexibility metrics
def calculate_routing_flexibility(event_log: pd.DataFrame) -> int:
    """
    Calculates the routing flexibility (number of variants in the event log)
    """
    return len(pm4py.get_variants(event_log))

# TODO: Check if routing flexibility has to be calculated based on the event log or the BPMN model
# TODO: Check how to handle loops in BPMN model (especially for flexibility)
# TODO: Also with simulated event logs: Calculate metrics based on the simulated event log or based on the provided BPMN model
# TODO: Key question: If i simulate a BPMN model and get an event log out of that, then reconvert it into a BPMN model, are the BPMN models the same?