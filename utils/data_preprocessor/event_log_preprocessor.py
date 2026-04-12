import pandas as pd
import csv

# Required event log columns 
required_event_log_columns = ["case:concept:name", "concept:name", "time:timestamp", "org:resource", "cost:amount"]

# Required event log column names
event_log_column_map = {
    "case:concept:name":["case_id", "case", "caseid", "case id", "instance_id", "instance", "instanceid", "instance id"],
    "concept:name":["activity", "activity_name", "event", "event_name", "task", "operation", "step"],
    "time:timestamp":["timestamp", "time", "datetime", "date", "eventtime"],
    "org:resource":["resource", "user", "worker", "agent", "performer"],
    "cost:amount":["cost", "costs"],
    "lifecycle:transition":["lifecycle", "transition", "event_type", "eventtype"]
}

def get_csv_delimiter(file_path: str) -> str:
    """
    Detect the delimiter used in an event log in CSV format
    """
    with open(file_path, 'r') as csv_file:
        delimiter = str(csv.Sniffer().sniff(csv_file.read()).delimiter)
        return delimiter

def rename_columns(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes event log column names to the canonical names expected by pm4Py
    """
    mapped = {}
    for canonical_col, synonyms in event_log_column_map.items():
        for column in event_log.columns:
            if column.lower().strip() in synonyms:
                mapped[column] = canonical_col
    event_log.rename(columns=mapped, inplace=True)
    event_log = event_log.loc[:, ~event_log.columns.duplicated(keep='first')]
    return event_log

def check_for_required_columns(event_log: pd.DataFrame) -> list:
    """
    Checks if the event log contains all required columns for process evaluation
    """
    return [col for col in required_event_log_columns if col not in event_log.columns]

def transform_data_types(event_log: pd.DataFrame) -> pd.DataFrame:
    """
    Converts data types into a format suitable for the event log analyzer
    """
    event_log["time:timestamp"] = pd.to_datetime(event_log["time:timestamp"], errors="coerce")

    event_log["case:concept:name"] = event_log["case:concept:name"].astype(str)

    event_log["cost:amount"] = pd.to_numeric(event_log["cost:amount"], errors="coerce")
        
    event_log.sort_values(by=["case:concept:name", "time:timestamp"], ascending=[True, True])
    return event_log