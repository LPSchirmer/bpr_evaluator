# Importing third-party libraries
import sys
import os

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom modules
from bpmn_model_analyzer.process_model_layer import *
from event_log_analyzer.as_is_metrics_analyzer import *

# Central process evaluation metrics with its associated hierarchy
evaluation_metrics = {
    "Process model view": {

        "Syntactic Quality": {

            "Structural Quality": {
                "Task sequence flows": None,
                "Start event sequence flows": None,
                "Split Gateways": None
            },

            "Behavioral Quality": {
                "Soundness": None
            }
        
        },

        "Semantic Quality": {

        },

        "Pragmatic Quality": {

            "Understandability": {
                "Number of Nodes": None,
                "Depth": None,
                "Coefficient of Connectivity": None
            },

            "Modifiability": {
                "Gateway Mismatch": None,
                "Density": None,
                "Sequentiality": None
            }

        }
    },
    "Operational process view": {

        "Time": {
            "Mean cycle time": None
        },

        "Cost": {
            "Mean process costs": None
        },

        "Quality": {
            "Rework rate": None
        },

        "Flexibility": {
            "Routing flexibility": None
        }

    },
    "Strategic process view": {
        "SubCriteria1": {

        },
        "SubCriteria2": {

        }
    }
}