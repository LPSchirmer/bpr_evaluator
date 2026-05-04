# Importing third-party libraries
import os
import sys
import pm4py

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom src module
from src.bpmn_model_analyzer.bpmn_data_extractor import *

def check_bpmn_for_new_tasks(event_log_tasks: list, bpmn_model_tasks: dict) -> dict:
    """
    Returns tasks in the BPMN model that are not present in the event log (potentially new tasks or faulty task names)
    """
    return {task_id: task_name for task_id, task_name in bpmn_model_tasks.items() if task_name not in event_log_tasks}

def find_new_xor_split_gateways(as_is_bpmn: pm4py.BPMN, to_be_bpmn: pm4py.BPMN) -> dict:
    """
    Compares the as-is and new BPMN model and returns a dictionary with the id's of the new gateways (XOR Split) as keys and the list of first target tasks as values
    """
    as_is = get_xor_split_gateway_target_tasks(as_is_bpmn)
    to_be = get_xor_split_gateway_target_tasks(to_be_bpmn)

    target_tasks_as_is = {tuple(sorted(tasks)) for tasks in as_is.values()}

    new_gateways = {}
    for g_id, tasks_to_be in to_be.items():

        if tuple(sorted(tasks_to_be)) not in target_tasks_as_is:
            new_gateways[g_id] = tasks_to_be

    return new_gateways