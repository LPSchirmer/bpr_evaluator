# Importing third-party libraries
import sys
import os
import pandas as pd
import pm4py
import copy

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom src modules
from src.bpmn_model_analyzer.process_model_layer import *
from src.event_log_analyzer.operational_layer import *

# Central quantitative process evaluation metrics with its associated hierarchy
evaluation_metrics = {
    "Process Model Dimension": {

        "Syntactic Quality": {

            "Structural Quality": {
                "Workflow Net": None
            },

            "Behavioral Quality": {
                "Soundness": None
            }
        
        },

        "Semantic Quality": {
            "Validity": {
                "Number of violated Validity Requirements": None
            },

            "Completeness": {
                "Number of violated Completeness Requirements": None
            }
        },

        "Pragmatic Quality": {

            "Understandability": {
                "Number of Nodes": None,
                "Average Gateway Degree": None
            },

            "Modifiability": {
                "Density": None,
                "Sequentiality": None
            }

        }
    },

    "Process Dimension": {

        "Time": {
            "Mean cycle time": None
        },

        "Cost": {
            "Mean process costs": None
        },

        "Quality": {
            "Repeatability": None
        },

        "Flexibility": {
            "Optionality": None
        }

    },

    "Organizational Dimension": {
        "Legal Feasability": {
            "Number of Legal Issues": None
        },

        "Schedule Feasability": {
            "Implementation Time": None
        }   
    }
}

# Description and unit of metrics for UI
evaluation_metrics_description = {
    "Workflow Net": {
        "description": "",
        "unit": "(1=yes, 0=no)"
    },
    "Soundness": {
        "description": "",
        "unit": "(1=yes, 0=no)"
    },
    "Number of violated Validity Requirements": {
        "description": "",
        "unit": "(#)"
    },
    "Number of violated Completeness Requirements": {
        "description": "",
        "unit": "(#)"
    },
    "Number of Nodes": {
        "description": "Represents the total number of nodes in the BPMN model, including activities, events, and gateways.",
        "unit": "(#)"
    },
    "Average Gateway Degree": {
        "description": "Represents the average of the number of both incoming and outgoing arcs of the gateway nodes in the BPMN model.",
        "unit": "Arcs per Gateway"
    },
    "Density": {
        "description": "Represents the ratio of the total number of arcs in the BPMN model to the maximum possible number of arcs.",
        "unit": "(0-1)"
    },
    "Sequentiality": {
        "description": "Represents the degree to which the BPMN model is constructed out of sequences of non-routing elements.",
        "unit": "(0-1)"
    },
    "Mean cycle time": {
        "description": "",
        "unit": "(min)"
    },
    "Mean process costs": {
        "description": "",
        "unit": "(€)"
    },
    "Repeatability": {
        "description": "",
        "unit": "(0-1)"
    },
    "Optionality": {
        "description": "",
        "unit": "(0-1)"
    },
    "Number of Legal Issues": {
        "description": "Number of internal and external compliance violations",
        "unit": "(#)"
    },
    "Implementation Time": {
        "description": "Estimated time (in days) required to implement the redesigned business process within the organization",
        "unit": "(days)"
    }
}

def calculate_process_metrics(event_log: pd.DataFrame, bpmn_model: pm4py.BPMN) -> dict:
    """
    Calculates quantitative process metrics for the given event log and BPMN model
    """
    metrics = copy.deepcopy(evaluation_metrics)

    # Process model metrics
    metrics["Process Model Dimension"]["Syntactic Quality"]["Structural Quality"]["Workflow Net"] = check_bpmn_model_is_workflow_net(bpmn_model)
    metrics["Process Model Dimension"]["Syntactic Quality"]["Behavioral Quality"]["Soundness"] = check_bpmn_model_for_soundness(bpmn_model)

    metrics["Process Model Dimension"]["Pragmatic Quality"]["Understandability"]["Number of Nodes"] = calculate_number_of_nodes(bpmn_model)
    metrics["Process Model Dimension"]["Pragmatic Quality"]["Understandability"]["Average Gateway Degree"] = calculate_average_gateway_degree(bpmn_model)
    metrics["Process Model Dimension"]["Pragmatic Quality"]["Modifiability"]["Density"] = calculate_density(bpmn_model)
    metrics["Process Model Dimension"]["Pragmatic Quality"]["Modifiability"]["Sequentiality"] = calculate_sequentiality(bpmn_model)

    # Process metrics
    metrics["Process Dimension"]["Time"]["Mean cycle time"] = calculate_mean_cycle_time(event_log)
    metrics["Process Dimension"]["Cost"]["Mean process costs"] = calculate_mean_process_costs(event_log)
    metrics["Process Dimension"]["Quality"]["Repeatability"] = calculate_repeatability(event_log)
    metrics["Process Dimension"]["Flexibility"]["Optionality"] = calculate_optionality(event_log)

    return metrics