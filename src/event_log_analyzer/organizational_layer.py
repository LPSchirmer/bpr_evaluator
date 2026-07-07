# Importing third-party libraries
import pm4py
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.algo.evaluation.replay_fitness import algorithm as fitness_evaluator
import pandas as pd

def calculate_degree_of_change(bpmn_model: pm4py.BPMN, event_log: pd.DataFrame) -> float:
    """
    Calculates the behavioral degree of change of a redesigned BPMN model in respect to the as-is process via conformance checking
    """
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)

    aligned_traces = alignments.apply(event_log, net, initial_marking, final_marking)
    fitness_result = fitness_evaluator.evaluate(aligned_traces, variant=fitness_evaluator.Variants.ALIGNMENT_BASED)

    log_fitness = fitness_result["log_fitness"]
    degree_of_change = 1.0 - log_fitness

    return degree_of_change

def get_process_variants(event_log: pd.DataFrame) -> list:
    """
    Returns a list with all variants, the process runs through
    """
    return list(pm4py.get_variants(event_log).keys())

def get_resources_per_task(event_log: pd.DataFrame) -> dict:
    """
    Returns a dictionary with all tasks and its associated resources in the event log
    """
    return event_log.groupby("concept:name")["org:resource"].unique().apply(list).to_dict()

def calculate_mean_cycle_time_per_variant(event_log: pd.DataFrame) -> dict:
    """
    Returns a dictionary with all variants and its associated mean cycle time (in minutes) in the event log
    """
    variants_duration = pm4py.get_variants_paths_duration(event_log)
    result = variants_duration.groupby("@@variant_column").agg(
        mean_variant_duration_minutes = ("@@flow_time", lambda x: x.sum()/60)
    ).to_dict()["mean_variant_duration_minutes"]
    return result