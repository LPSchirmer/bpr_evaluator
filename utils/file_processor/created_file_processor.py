import os
import pm4py
import pandas as pd

def create_path_for_created_visualizations(folder_path: str, created_file: str) -> str:
    """
    Creates and returns the path to store a created visualization
    """
    return os.path.join(folder_path, f"vis_{created_file}.jpeg")

def save_bpmn_visualization(event_log: pd.DataFrame, file_path: str) -> None:
    """
    Discovers the BPMN model of an event log and stores its visualization at the specified file path
    """
    bpmn_model = pm4py.discover_bpmn_inductive(event_log)
    pm4py.save_vis_bpmn(bpmn_model, file_path)