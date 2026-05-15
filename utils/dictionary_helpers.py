# Importing third-party libraries
from typing import Any

def extract_metrics_from_dicts(dicts_list: list) -> dict:
    """
    Extracts metrics from event log dict and BPMN dict and returns them in a more flattened way
    """
    def flatten(node: Any, res: dict) -> None:
        """
        Traverses the dict, flattens it and transforms data formats
        """
        if not isinstance(node, dict):
            return
        
        for k, v in node.items():
            if isinstance(v, dict):
                flatten(v, res)
            elif isinstance(v, bool):
                res[k] = 1.0 if v else 0.0
            elif isinstance(v, (int, float)):
                res[k] = float(v)

    all_metrics = {}

    for data_dict in dicts_list:
        # Event log dict
        if "event_log_name" in data_dict:
            display_name = f"{data_dict["event_log_name"]} (adjusted as-is process)"
            flat_results = {}
            flatten(data_dict.get("metrics", {}).get("adjusted_metrics", {}), flat_results)
            all_metrics[display_name] = flat_results
        
        # BPMN dict
        else:
            for key, content in data_dict.items():

                if isinstance(content, dict) and "metrics" in content:
                    flat_results = {}
                    flatten(content["metrics"], flat_results)
                    all_metrics[key] = flat_results

    return all_metrics