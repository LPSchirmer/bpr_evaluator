# Importing third-party libraries
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import pm4py
import sys
import os
import uuid
from datetime import datetime
from itertools import combinations
import os
from dotenv import load_dotenv
import json

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom src modules
from src.bpmn_model_analyzer.bpmn_data_extractor import *
from src.event_log_analyzer.simulation_parameter_extractor import *
from src.event_log_analyzer.organizational_layer import *
from src.process_evaluator.process_metrics_calculator import *
from src.process_evaluator.llm_evaluator import *
from src.process_evaluator.ahp_engine import *
from src.process_simulator.process_simulation_engine import *
from src.process_elements_mapper import *

# Importing custom utils modules
from utils.data_preprocessor.event_log_preprocessor import *
from utils.file_processor.created_file_processor import *
from utils.file_processor.uploaded_file_processor import *
from utils.dictionary_helpers import *

load_dotenv()

# Initialization of session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "step" not in st.session_state:
    st.session_state.step = 0

if "folder_path" not in st.session_state:
    st.session_state.folder_path = None

if "visualizations_folder_path" not in st.session_state:
    st.session_state.visualizations_folder_path = None

if "event_log" not in st.session_state:
    st.session_state.event_log = None

if "bpmn_models" not in st.session_state:
    st.session_state.bpmn_models = {}

if "upload_count" not in st.session_state:
    st.session_state.upload_count = 1

if "submitted_new_tasks_gateways" not in st.session_state:
    st.session_state.submitted_new_tasks_gateways = True

if "contextual_data" not in st.session_state:
    st.session_state.contextual_data = {
        "name_of_organization": None,
        "name_of_process": None,
        "industry": None,
        "number_of_employees": None,
        "revenue_per_year": None,
        "size": None,
        "experience_bpr": None,
        "form_submitted": False
    }

if "criteria_pairwise_comparisons" not in st.session_state:
    st.session_state.criteria_pairwise_comparisons = None

if "evaluation_results" not in st.session_state:
    st.session_state.evaluation_results = None

# Methods for updating session state
def next_step() -> None:
    if st.session_state.step < len(entry_stages) - 1:
        st.session_state.step += 1

def add_event_log_to_session_state(event_log_name: str, event_log: pd.DataFrame) -> None:
    st.session_state.event_log = {
        "event_log_name": event_log_name,
        "event_log": event_log,
        "tasks": [],
        "number_of_resources": None,
        "inductive_bpmn_model": None,
        "file_path_bpmn": None,
        "number_of_simulation_runs": None,
        "simulated_as_is_process": None,
        "metrics": {
            "as_is_metrics": {},
            "simulated_metrics": {},
            "adjusted_metrics": {}
        },
        "ai_explanation": {
            "Number of violated Completeness Requirements": None,
            "Number of Legal Issues": None,
            "Implementation Time": None
        },
        "process_variants": None       
    }

def add_bpmn_model_to_session_state(bpmn_model_name: str, bpmn_model: pm4py.BPMN) -> None:
    st.session_state.bpmn_models[bpmn_model_name] = {
        "model": bpmn_model,
        "file_path": None,
        "tasks": {},
        "new_tasks": {},
        "new_xor_split_gateways": None,
        "simulation_parameters": {
            "arrival_time": None,
            "processing_times": {},
            "costs": {},
            "new_gateway_probabilities": {}
        },
        "simulated_event_log": {},
        "metrics": {},
        "form_submitted": False,
        "ai_explanation": {
            "Number of violated Completeness Requirements": None,
            "Number of Legal Issues": None,
            "Implementation Time": None
        },
        "degree_of_change": None,
        "process_variants": None
    }

# Page metadata
icon = "📈"
st.set_page_config(page_title="EAE4GP - Start Evaluation", page_icon=icon, layout="wide")

# Header and description
st.title(f"{icon} EAE4GP - Ex-Ante Evaluation for Goal-Driven Prioritization of Redesigned Business Process Alternatives")
st.markdown("Welcome to EAE4GP - a prototypical instantiation of the reference architecture from my bachelor thesis with the title 'Choosing the Right Path: Ex-Ante Evaluation for Goal-Driven Prioritization or Redesigned Business Process Alternatives'.")
st.markdown("EAE4GP is designed to support process designers in evaluating the impact of their redesigned business processes prior to implementation by prioritizing alternatives based on individual context and goals. Therefore, it provides systematic decision-support regarding which alternative should be chosen and implemented.")
st.divider()

# Upload section
st.header("Start the Evaluation by uploading your data")

entry_stages = [
    "1. Upload as-is process",
    "2. Upload to-be processes",
    "3. Specifiy context",
    "4. Weight evaluation criteria"
]

upload_columns = st.columns(len(entry_stages))

for column, entry_stage in zip(upload_columns, entry_stages):
    with column:
        with st.container(border=True):
            st.markdown(f"**{entry_stage}**")

if not st.session_state.evaluation_results:

    # Step 1: Upload event log
    # TODO: Check file storing methodology in uploads folder
    if st.session_state.step == 0:

        with upload_columns[0]:
            st.divider()
        st.subheader(entry_stages[0])

        event_log = st.file_uploader("Upload an event log of the as-is process. It should at least contain the following columns: case:concept:name, concept:name, time:timestamp, cost:amount, and org:resource.", 
                                     type=["csv", "xes"], 
                                     key="event_log_uploader")
        
        if event_log:
            upload_date = datetime.now().strftime("%Y-%m-%d")
            session_folder_path = create_folder_for_upload("uploads", f"{st.session_state.session_id}-{upload_date}")
            st.session_state.folder_path = session_folder_path

            event_log_folder_path = create_folder_for_upload(st.session_state.folder_path, "event_log")
            file_path = create_path_for_uploaded_file(event_log_folder_path, event_log)

            save_uploaded_file(event_log, file_path)

            file_suffix = get_file_extension(event_log.name)

            if file_suffix == ".csv":
                df = pd.read_csv(file_path, delimiter=get_csv_delimiter(file_path))

            elif file_suffix == ".xes":
                df = pm4py.read_xes(file_path)

            else:
                st.error("Unsupported file type for event logs. Please upload a CSV or XES file.", icon="🚨")
                st.stop()
            
            st.markdown("Processed event log:")
            st.write(df.head())

            df = rename_columns(df)

            if "time:start_timestamp" in df.columns and "time:completion_timestamp" in df.columns:
                df = restructure_event_log(df)

            missing_columns = check_for_required_columns(df)
            
            if not missing_columns:
                df = transform_data_types(df)

                df = drop_rows_with_null_values(df)

                df = pm4py.filter_variants_top_k(df, k=5)

                event_log_name = event_log.name.replace(get_file_extension(event_log.name), "")

                add_event_log_to_session_state(event_log_name, df)

                st.session_state.event_log["tasks"] = get_tasks(st.session_state.event_log["event_log"])
                st.session_state.event_log["inductive_bpmn_model"] = pm4py.discover_bpmn_inductive(st.session_state.event_log["event_log"])
                st.session_state.event_log["number_of_resources"] = get_number_of_resources(st.session_state.event_log["event_log"])

                event_log_bpmn_folder_path = create_folder_for_upload(event_log_folder_path, "bpmn_model")
                file_path = os.path.join(event_log_bpmn_folder_path, st.session_state.event_log["event_log_name"])

                pm4py.write_bpmn(st.session_state.event_log["inductive_bpmn_model"], file_path)

                st.session_state.event_log["file_path_bpmn"] = file_path + ".bpmn"

                number_of_process_instances = calculate_number_of_process_instances(st.session_state.event_log["event_log"])

                st.session_state.event_log["number_of_simulation_runs"] = 2000

                st.session_state.event_log["metrics"]["as_is_metrics"] = calculate_process_metrics(st.session_state.event_log["event_log"], st.session_state.event_log["inductive_bpmn_model"])
            
                st.success("Event log uploaded successfully! You can now proceed to the next step to upload BPMN models of the to-be processes.", icon="✅")
            else:
                st.error(f"The uploaded event log is missing the following required columns: {', '.join(missing_columns)}", icon="🚨")

    # Step 2: Upload BPMN models, check for elements that are not present in the provided event log, add those elements by user input and simulate the models
    elif st.session_state.step == 1:

        if st.session_state.event_log["simulated_as_is_process"] is None:
            with st.spinner(f"Simulating {st.session_state.event_log['event_log_name']} to extract metrics for the adjusted as-is process..."):
                
                # Simulate as-is process for assessing the simulation deviation and adjusting the metrics of the as-is process accordingly
                as_is_simulated = start_monte_carlo_simulation(st.session_state.event_log["inductive_bpmn_model"],
                                                               st.session_state.event_log["inductive_bpmn_model"],
                                                               st.session_state.event_log["event_log"], 
                                                               {}, 
                                                               {}, 
                                                               st.session_state.event_log["number_of_simulation_runs"], 
                                                               calculate_arrival_time_statistics(st.session_state.event_log["event_log"])["arrival_time_mean"],
                                                               st.session_state.event_log["number_of_resources"])
                
                as_is_simulated = rename_columns(as_is_simulated)
                as_is_simulated_costs = get_costs_per_activity(st.session_state.event_log["event_log"])
                as_is_simulated["cost:amount"] = as_is_simulated["concept:name"].map(as_is_simulated_costs)
                as_is_simulated = transform_data_types(as_is_simulated)
                st.session_state.event_log["simulated_as_is_process"] = as_is_simulated

                st.session_state.event_log["metrics"]["simulated_metrics"] = calculate_process_metrics(as_is_simulated, 
                                                                                                       st.session_state.event_log["inductive_bpmn_model"])
                
                st.session_state.event_log["metrics"]["adjusted_metrics"]["Process Model Dimension"] = st.session_state.event_log["metrics"]["as_is_metrics"]["Process Model Dimension"]

                pd_as_is = st.session_state.event_log["metrics"]["as_is_metrics"]["Process Dimension"]
                pd_to_be = st.session_state.event_log["metrics"]["simulated_metrics"]["Process Dimension"]

                st.session_state.event_log["metrics"]["adjusted_metrics"]["Process Dimension"] = {
                    cat: {met: (pd_as_is[cat][met] + pd_to_be[cat][met]) / 2 for met in pd_as_is[cat]}
                    for cat in pd_as_is
                }

                st.session_state.event_log["metrics"]["adjusted_metrics"]["Organizational Dimension"] = st.session_state.event_log["metrics"]["as_is_metrics"]["Organizational Dimension"]
                
                st.toast(f"Simulation for {st.session_state.event_log['event_log_name']} finished!", icon="🚀")

        with upload_columns[1]:
            st.divider()

        st.subheader(entry_stages[1])
        st.warning("If the redesigned BPMN model contains tasks that are already present in the event log of the as-is process, please ensure that they share the exact same names to enable proper mapping.", icon="⚠️")
        
        visualizations_folder_path = create_folder_for_upload(st.session_state.folder_path, "visualizations")
        st.session_state.visualizations_folder_path = visualizations_folder_path

        multiple_to_be_processes_columns = st.columns(2)
        with multiple_to_be_processes_columns[0]:
            if st.button("Add another redesigned process", icon="➕", use_container_width=True):
                st.session_state.upload_count += 1
                st.rerun()

        with multiple_to_be_processes_columns[1]:
            if st.button("Delete the last uploaded redesigned process", icon="➖", use_container_width=True, disabled=st.session_state.upload_count == 1):
                if st.session_state.upload_count > 1:
                    st.session_state.upload_count -= 1
                    st.rerun()

        for i in range(st.session_state.upload_count):
            bpmn_model_raw = st.file_uploader(f"Upload a BPMN model of the to-be process ({i+1})", type=["bpmn"], key=f"bpmn_uploader_{i}")
            
            if bpmn_model_raw:
                bpmn_model_name = bpmn_model_raw.name.replace(get_file_extension(bpmn_model_raw.name), "")
                
                if bpmn_model_name not in st.session_state.bpmn_models:
                    bpmn_model_folder_path = create_folder_for_upload(st.session_state.folder_path, "bpmn")
                    file_path = create_path_for_uploaded_file(bpmn_model_folder_path, bpmn_model_raw)
                    save_uploaded_file(bpmn_model_raw, file_path)
                    
                    bpmn_model = pm4py.read_bpmn(file_path)
                    add_bpmn_model_to_session_state(bpmn_model_name, bpmn_model)
                    
                    st.session_state.bpmn_models[bpmn_model_name]["file_path"] = file_path
                    st.session_state.bpmn_models[bpmn_model_name]["tasks"] = get_bpmn_tasks(bpmn_model)
                    st.session_state.bpmn_models[bpmn_model_name]["new_tasks"] = check_bpmn_for_new_tasks(st.session_state.event_log["tasks"], st.session_state.bpmn_models[bpmn_model_name]["tasks"])
                    st.session_state.bpmn_models[bpmn_model_name]["new_xor_split_gateways"] = find_new_xor_split_gateways(st.session_state.event_log["inductive_bpmn_model"], st.session_state.bpmn_models[bpmn_model_name]["model"])

                # Helper variables for shorter code
                current_model_data = st.session_state.bpmn_models[bpmn_model_name]
                file_path = current_model_data["file_path"]

                if current_model_data["new_tasks"] or current_model_data["new_xor_split_gateways"]:
                    st.session_state.submitted_new_tasks_gateways = False

                    with st.expander(f"Add missing simulation specifications for {bpmn_model_name}" if not current_model_data["form_submitted"] else f"Data for {bpmn_model_name} saved!", 
                                    icon = "✅" if current_model_data["form_submitted"] else None, 
                                    expanded = True if not current_model_data["form_submitted"] else False):

                        with st.form(f"form_{bpmn_model_name}_{i}"):
                            
                            # Visualized BPMN model of process
                            file_path_vis = create_path_for_created_visualizations(st.session_state.visualizations_folder_path, bpmn_model_name)
                            pm4py.save_vis_bpmn(current_model_data["model"], file_path_vis)
                            st.image(file_path_vis, caption=f"BPMN visualization of {bpmn_model_name}", width="stretch")
                            st.divider()
                            
                            # Tasks section
                            if current_model_data["new_tasks"]:
                                st.subheader("Tasks")
                                st.markdown(f"{bpmn_model_name} contains the following tasks that are not present in the event log of the as-is process: :gray-badge[{', '.join(current_model_data["new_tasks"].values())}]. Please estimate the duration and cost of these tasks for accurate simulation.")

                                overall_mean_activity_duration = round(sum(get_mean_activity_duration(st.session_state.event_log["event_log"]).values()) / len(get_mean_activity_duration(st.session_state.event_log["event_log"]).values()) / 60, 2)
                                # TODO: Check if Euro is correct
                                overall_mean_activity_cost = round(sum(get_costs_per_activity(st.session_state.event_log["event_log"]).values()) / len(get_costs_per_activity(st.session_state.event_log["event_log"]).values()), 2)
                                st.info(f"Tip: Based on the event log, tasks take an average of {overall_mean_activity_duration} minutes and cost about €{overall_mean_activity_cost} (see prefilled values).", icon="ℹ️")
                                
                                for tid, tname in current_model_data["new_tasks"].items():
                                    st.markdown(f"**{tname}**")
                                    # TODO: Check better input format for duration
                                    st.number_input("Duration [min]", min_value=0.0, step=0.1, value=overall_mean_activity_duration, key=f"time_{bpmn_model_name}_{tname}")
                                    st.number_input("Cost [€]", min_value=0.0, step=0.1, value=overall_mean_activity_cost, key=f"cost_{bpmn_model_name}_{tname}")
                                    
                                    st.divider()

                            # Gateway section
                            # TODO: Check if not more than 100% and check prefilled values, tip for filling out values
                            if current_model_data["new_xor_split_gateways"]:
                                st.subheader("Gateways")
                                
                                for g_id, flows in current_model_data["new_xor_split_gateways"].items():
                                    st.markdown("XOR Split Gateway")

                                    for flow_id, targets in flows.items():
                                        target_names = f":gray-badge[{", ".join(targets)}]"
                                        
                                        st.number_input(
                                            label=f"Flow with the following target tasks: {target_names} | Probability of execution (0-100%)",
                                            min_value=0,
                                            max_value=100,
                                            value=int(100 / len(flows)),
                                            key=f"prob_{bpmn_model_name}_{g_id}_{flow_id}" 
                                        )
                                    st.divider()

                            # Form Submit
                            if st.form_submit_button(f"Submit data for {bpmn_model_name}", use_container_width=True):
                                
                                # Transfer data from widgets into session state
                                for tid, tname in current_model_data["new_tasks"].items():
                                    current_model_data["simulation_parameters"]["processing_times"][tname] = st.session_state[f"time_{bpmn_model_name}_{tname}"] * 60
                                    current_model_data["simulation_parameters"]["costs"][tname] = st.session_state[f"cost_{bpmn_model_name}_{tname}"]
                                
                                for g_id, flows in current_model_data["new_xor_split_gateways"].items():
                                    current_model_data["simulation_parameters"]["new_gateway_probabilities"][g_id] = {}

                                    for flow_id, targets in flows.items():
                                        prob_key = f"prob_{bpmn_model_name}_{g_id}_{flow_id}"

                                        if prob_key in st.session_state:
                                            path_probability = st.session_state[prob_key] / 100

                                            for task_name in targets:
                                                current_model_data["simulation_parameters"]["new_gateway_probabilities"][g_id][task_name] = path_probability
                                
                                current_model_data["form_submitted"] = True
                                st.rerun()
                
                # Simulation
                if current_model_data.get("form_submitted") or (not current_model_data["new_tasks"] and not current_model_data["new_xor_split_gateways"]):
                    st.session_state.submitted_new_tasks_gateways = True

                    if f"simulated_{bpmn_model_name}" not in current_model_data["simulated_event_log"]:

                        with st.spinner(f"Simulating {bpmn_model_name}..."):

                            current_model_data["simulation_parameters"]["arrival_time"] = calculate_arrival_time_statistics(st.session_state.event_log["event_log"])["arrival_time_mean"]
                            
                            # Map existing tasks
                            for b_tid, b_tname in current_model_data["tasks"].items():
                                if b_tname in st.session_state.event_log["tasks"]:
                                    current_model_data["simulation_parameters"]["processing_times"][b_tname] = get_mean_activity_duration(st.session_state.event_log["event_log"])[b_tname]
                                    current_model_data["simulation_parameters"]["costs"][b_tname] = get_costs_per_activity(st.session_state.event_log["event_log"])[b_tname]
                            
                            # Start simulation with all parameters
                            df_sim = start_monte_carlo_simulation(current_model_data["model"],
                                                                  st.session_state.event_log["inductive_bpmn_model"], 
                                                                  st.session_state.event_log["event_log"], 
                                                                  current_model_data["simulation_parameters"]["processing_times"], 
                                                                  current_model_data["simulation_parameters"]["new_gateway_probabilities"], 
                                                                  st.session_state.event_log["number_of_simulation_runs"], 
                                                                  current_model_data["simulation_parameters"]["arrival_time"],
                                                                  st.session_state.event_log["number_of_resources"])
                            
                            # Preprocess simulated event log
                            df_sim = rename_columns(df_sim)
                            df_sim["cost:amount"] = df_sim["concept:name"].map(current_model_data["simulation_parameters"]["costs"])
                            df_sim = transform_data_types(df_sim)
                            
                            # Transfer simulated log to session state and calculate metrics
                            current_model_data["simulated_event_log"][f"simulated_{bpmn_model_name}"] = df_sim
                            current_model_data["metrics"] = calculate_process_metrics(current_model_data["simulated_event_log"][f"simulated_{bpmn_model_name}"], current_model_data["model"])
                            st.toast(f"Simulation for {bpmn_model_name} finished!", icon="🚀")

    elif st.session_state.step == 2:
        with upload_columns[2]:
            st.divider()

        st.subheader(entry_stages[2])
        st.markdown("Since business processes are not generic, but highly domain-dependent, contextual information is crucial for a useful evaluation. Therefore, please provide the following contextual data for a tailor-made evaluation.")

        with st.expander("Provide contextual data" if not st.session_state.contextual_data["form_submitted"] else f"Contextual data successfully submitted!", 
                                    icon = "✅" if st.session_state.contextual_data["form_submitted"] else None, 
                                    expanded = True if not st.session_state.contextual_data["form_submitted"] else False):
            
            with st.form("contextual_input_form"):

                st.subheader("Organization-related information")
                st.markdown("**Name of your Organization**")
                st.text_input(
                    "Type in the name of your organization for contextual data enrichment",
                    placeholder="Name of your organization",
                    key="name_of_organization"
                )

                st.divider()
                st.markdown("**Compliance Requirements**")
                compliance_requirements = st.file_uploader("Upload files that describe the **internal and external compliance requirements** that the **business process** must meet", 
                                                type=["pdf", "txt"],
                                                help="Internal requirements need to be fully specified, while the name of an external requirement is sufficient for external research",
                                                accept_multiple_files=True, 
                                                key=f"compliance_requirements_uploader")
                
                st.divider()
                st.subheader("Process-related information")
                st.markdown("**Name of the Process**")
                st.text_input(
                    "Type in the name of your process",
                    placeholder="E.g. Order to Cash, Purchase to Order ...",
                    key="name_of_process"
                )

                st.divider()
                completeness_requirements = st.file_uploader("Upload files that describe **completeness requirements** for the **business process model**", 
                                                        type=["pdf", "txt"],
                                                        help="Completeness ensures that the model contains all relevant statements about the corresponding business process (e. g. Activity 'A' must be present in the model, all activities must be placed within a lane ...)",
                                                        accept_multiple_files=True, 
                                                        key=f"completeness_requirements_uploader"
                                                    )
                st.divider()
                
                if st.form_submit_button("Submit contextual data", use_container_width=True):

                    st.session_state.contextual_data["name_of_organization"] = st.session_state["name_of_organization"]
                    st.session_state.contextual_data["name_of_process"] = st.session_state["name_of_process"]
                    st.session_state.contextual_data["form_submitted"] = True
                    st.rerun()

        if st.session_state.contextual_data.get("form_submitted"):

            with st.spinner("Processing your contextual information..."):

                # Organizational Context
                organizational_context_research = client_gemini.models.generate_content(
                    model = os.getenv("GEMINI_MODEL"), 
                    contents = f"""Research the organization '{st.session_state.contextual_data["name_of_organization"]}' and fill out the following data:
                        - industry in which the organization operates
                        - total employee count in the year {last_year}. If this data is not available, refer to the year {second_to_last_year} or {third_to_last_year}
                        - revenue for the year {last_year} with its local currency. If this data is not available, refer to the year {second_to_last_year} or {third_to_last_year}
                        - classification of the organization size according to these rules: '{json.dumps(company_size_classification)}'
                        - assessment whether the organization is experienced with business process management methodologies and especially business process improvement/redesign/innovation projects. 
                          Base this assessment on publicy availiable data that shows past experiences (e. g. business process management/improvement/redesign/innovation achievements and failures). 
                          The experiences must have a business process focus. Do not incorporate product improvements/innovations.""",
                    config = types.GenerateContentConfig(
                        system_instruction=system_prompts["organizational_context_research"],
                        temperature=0.0,
                        tools=[search_tool]
                    )
                )

                organizational_context = client_gemini.models.generate_content(
                    model=os.getenv("GEMINI_MODEL"),
                    contents= f"Organize this research: '{organizational_context_research.text}' in the required format.",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompts["organizational_context"],
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=OrganizationalContext
                    )
                )

                for key, value in organizational_context.parsed:
                    st.session_state.contextual_data[key] = value

                compliance_requirements_folder_path = create_folder_for_upload(st.session_state.folder_path, "compliance_requirements")
                compliance_requirements_upload_ai = []

                for compliance_requirement in compliance_requirements:
                    file_path = create_path_for_uploaded_file(compliance_requirements_folder_path, compliance_requirement)
                    save_uploaded_file(compliance_requirement, file_path)
                    file_suffix = get_file_extension(compliance_requirement.name)

                    requirement_upload_ai = upload_file_to_llm(file_path, file_suffix)
                    compliance_requirements_upload_ai.append(requirement_upload_ai)

                compliance_evaluation_research = client_gemini.models.generate_content(
                    model = os.getenv("GEMINI_MODEL"), 
                    contents = f"""
                        Provided Input: 
                        - Compliance requirements: {compliance_requirements_upload_ai}
                        Context:
                        - Organization: {st.session_state.contextual_data["name_of_organization"]}
                        - Industry: {st.session_state.contextual_data["industry"]}
                        - Business Process: {st.session_state.contextual_data["name_of_process"]}
                        - Current Year: {current_year}
                        Tasks:
                        1. Differentiate provided norms: Analyze the provided input. Distinguish between internal norms (company-specific policies, internal SOPs) and external norms (laws, ISO standards, GDPR, etc.). 
                            Action: Ignore internal norms. Only research and summarize external norms (identified by name, number, or official title).
                        2. Web Research (General): Independently research applicable external laws or regulations for the year {current_year} that are specifically relevant to this business process.
                            Constraint: Identify a maximum of 3 independent external norms. If no highly relevant norms are found, do not hallucinate: list fewer or none.
                        3. Synthesis: Combine the researched norms with the relevant external norms found in the provided input.
                        Critical Requirements:
                        - BPMN Auditability: ONLY incorporate norms that can be verified by looking at a BPMN model. This means the norm must relate to:
                            - The sequence of activities (control flow)
                            - Specific tasks or gateways
                            - Resource assignments (Who/What is responsible for a task)
                        - Process Specificity: Do not include broad industry standards unless they apply directly to the steps of the process '{st.session_state.contextual_data["name_of_process"]}'
                        - Year Accuracy: All regulations must be valid for {current_year}""",
                    config = types.GenerateContentConfig(
                        system_instruction=system_prompts["compliance_evaluation_research"],
                        temperature=0.0,
                        tools=[search_tool]
                    )
                )
                
                as_is_bpmn_model_upload_ai = upload_file_to_llm(st.session_state.event_log["file_path_bpmn"], ".bpmn")

                def compliance_evaluation_ai(bpmn_model, event_log, as_is=True):

                    resources_data = json.dumps(get_resources_per_task(st.session_state.event_log["event_log"]))

                    instructions = f"""
                            Your task is to evaluate a business process (in BPMN form) against internal and external compliance requirements.
                            Provided input:
                            1. BPMN model: See attached BPMN XML file
                            2. Resources per task: {resources_data if as_is else "No resource data provided for the process. Ignore all resource-related compliance requirements."}
                            3. Mean cycle time in minutes per process variant: {calculate_mean_cycle_time_per_variant(event_log)}
                            4. Research results (External norms): {compliance_evaluation_research.text}
                            5. Directly provided requirements: See attached documentes
                            Evaluation rules:
                            You must distinguish between two types of requirements:
                            1. Mandatory evaluation (Internal & external that are explicitly provided)
                                - Scope: All internal company policies and any external norms that were explicitly uploaded/provided by the user
                                - Task: Evaluate the process against these requirements. Identify violations, non-compliant activities, and structural gaps
                            2. Strict 100% evidence rule (Researched external norms)
                                - Scope: Norms that were found via web research but were NOT in the original user documents
                                - Constraint: ONLY perform an evaluation if the provided process data (BPMN & Resources) allows for a 100% certain conclusion
                                - Incomplete Data: If the process data is insufficient to definitively prove compliance or a violation, do not evaluate this requirement. Do not make assumptions or "best guesses"
                            Output requirements:
                                - Analyze the control flow, gateways, and resource assignments
                                - Map every identified violation to a specific task or structural element in the BPMN
                                - If a researched norm is skipped due to insufficient data, do not list it as a violation"""
                    
                    prompt_content = [bpmn_model]
                    prompt_content += compliance_requirements_upload_ai
                    prompt_content.append(instructions)

                    compliance_evaluation = client_gemini.models.generate_content(
                        model=os.getenv("GEMINI_MODEL"), 
                        contents=prompt_content,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompts["compliance_evaluation"],
                            temperature=0.0,
                            response_mime_type="application/json",
                            response_schema=Compliance
                        )
                    )
                    return compliance_evaluation
                
                res_parsed = compliance_evaluation_ai(as_is_bpmn_model_upload_ai, st.session_state.event_log["event_log"]).parsed
                st.session_state.event_log["metrics"]["adjusted_metrics"]["Organizational Dimension"]["Legal Feasability"]["Number of Legal Issues"] = res_parsed.violations
                st.session_state.event_log["ai_explanation"]["Number of Legal Issues"] = {item.violated_compliance_rule: item.description for item in res_parsed.explanation}
                
                client_gemini.files.delete(name=as_is_bpmn_model_upload_ai.name)

                for bpmn_model_name, bpmn_model_data in st.session_state.bpmn_models.items():

                    bpmn_model_upload_ai = upload_file_to_llm(bpmn_model_data["file_path"], ".bpmn")

                    res_parsed = compliance_evaluation_ai(bpmn_model_upload_ai, bpmn_model_data["simulated_event_log"][f"simulated_{bpmn_model_name}"], as_is=False).parsed
                    st.session_state.bpmn_models[bpmn_model_name]["metrics"]["Organizational Dimension"]["Legal Feasability"]["Number of Legal Issues"] = res_parsed.violations
                    st.session_state.bpmn_models[bpmn_model_name]["ai_explanation"]["Number of Legal Issues"] = {item.violated_compliance_rule: item.description for item in res_parsed.explanation}

                    client_gemini.files.delete(name=bpmn_model_upload_ai.name)

                for req_file in compliance_requirements_upload_ai:
                    client_gemini.files.delete(name=req_file.name)

                completeness_requirements_folder_path = create_folder_for_upload(st.session_state.folder_path, "completeness_requirements")
                completeness_requirements_upload_ai = []

                for completeness_requirement in completeness_requirements:
                    file_path = create_path_for_uploaded_file(completeness_requirements_folder_path, completeness_requirement)
                    save_uploaded_file(completeness_requirement, file_path)
                    file_suffix = get_file_extension(completeness_requirement.name)

                    completeness_requirement_upload_ai = upload_file_to_llm(file_path, file_suffix)

                    completeness_requirements_upload_ai.append(completeness_requirement_upload_ai)
                    
                as_is_bpmn_model_upload_ai = upload_file_to_llm(st.session_state.event_log["file_path_bpmn"], ".bpmn")

                st.session_state.event_log["process_variants"] = get_process_variants(st.session_state.event_log["event_log"])
                        
                def semantic_evaluation_ai(bpmn_model, process_variants):

                    semantic_evaluation = client_gemini.models.generate_content(
                        model = os.getenv("GEMINI_MODEL"), 
                        contents = [bpmn_model] + 
                        completeness_requirements_upload_ai + 
                        [f"""Carefully evaluate the attached BPMN model against the provided business process requirements regarding 
                            the semantic quality criterion 'Completeness'. Completeness means that all relevant elements 
                            (e. g. activities, events, gateways, sequence flows, resources, etc.) 
                            described in the business process model requirements are actually present in the business process model.
                            Paths in the BPMN model: {process_variants}
                         """],
                        config = types.GenerateContentConfig(
                            system_instruction=system_prompts["semantic_evaluation"],
                            temperature=0.0,
                            response_mime_type="application/json",
                            response_schema=Semantic
                        )
                    )
                    return semantic_evaluation

                res_parsed = semantic_evaluation_ai(as_is_bpmn_model_upload_ai, st.session_state.event_log["process_variants"]).parsed
                st.session_state.event_log["metrics"]["adjusted_metrics"]["Process Model Dimension"]["Semantic Quality"]["Completeness"]["Number of violated Completeness Requirements"] = res_parsed.violations
                st.session_state.event_log["ai_explanation"]["Number of violated Completeness Requirements"] = {item.violated_requirement: item.description for item in res_parsed.explanation}

                client_gemini.files.delete(name=as_is_bpmn_model_upload_ai.name)

                for bpmn_model_name, bpmn_model_data in st.session_state.bpmn_models.items():

                    bpmn_model_upload_ai = upload_file_to_llm(bpmn_model_data["file_path"], ".bpmn")
                    bpmn_model_data["process_variants"] = get_process_variants(bpmn_model_data["simulated_event_log"][f"simulated_{bpmn_model_name}"])

                    res_parsed = semantic_evaluation_ai(bpmn_model_upload_ai, bpmn_model_data["process_variants"]).parsed
                    st.session_state.bpmn_models[bpmn_model_name]["metrics"]["Process Model Dimension"]["Semantic Quality"]["Completeness"]["Number of violated Completeness Requirements"] = res_parsed.violations
                    st.session_state.bpmn_models[bpmn_model_name]["ai_explanation"]["Number of violated Completeness Requirements"] = {item.violated_requirement: item.description for item in res_parsed.explanation}
                
                    client_gemini.files.delete(name=bpmn_model_upload_ai.name)

                for req_file in completeness_requirements_upload_ai:
                    client_gemini.files.delete(name=req_file.name)

                schedule_evaluation_research = client_gemini.models.generate_content(
                        model = os.getenv("GEMINI_MODEL"), 
                        contents = f"""Conduct a research into the business process '{st.session_state.contextual_data["name_of_process"]}' 
                                    specifically within the '{st.session_state.contextual_data["industry"]}' sector.
                                    Your goal is to provide the structural context needed for a subsequent implementation effort estimation of a redesigned business process alternative. 
                                    Focus on:
                                    - Upstream & Downstream Dependencies: Map out which typical core processes provide input to this process and which ones rely on its output. 
                                    - Process Centrality: How critical is this process to the overall value chain of a '{st.session_state.contextual_data["industry"]}' company? (e.g., Is it a standalone support process or a deeply intertwined core process?)
                                    - Stakeholder & System Complexity: List the typical departments involved and the standard IT systems this process interacts with. Be highly specific about whether typical interactions are manual or automated, to avoid overestimating technical complexity later.
                                    - Related implementation effort: Based on the existing experiences of organizations 
                                      (approx. {st.session_state.contextual_data["revenue_per_year"]} revenue 
                                      and {st.session_state.contextual_data["number_of_employees"]} employees),
                                      how long does the implementation of a redesigned business process typically last? 
                                      Provide these estimates as a lean baseline, emphasizing the minimum viable time required for a transition without excessive project overhead.
                                      Crucially, your time estimate must strictly start from the moment the conceptual redesign is already finalized. 
                                      Estimate only the net duration for the actual rollout and stabilization, excluding any prior discovery or BPMN modeling phases.""",
                        config = types.GenerateContentConfig(
                            system_instruction=system_prompts["schedule_evaluation_research"],
                            temperature=0.0,
                            tools=[search_tool]
                        )
                )

                st.session_state.event_log["metrics"]["adjusted_metrics"]["Organizational Dimension"]["Schedule Feasability"]["Implementation Time"] = 0

                for bpmn_model_name, bpmn_model_data in st.session_state.bpmn_models.items():

                    bpmn_model_upload_ai = upload_file_to_llm(bpmn_model_data["file_path"], ".bpmn")

                    bpmn_model_data["degree_of_change"] = calculate_degree_of_change(bpmn_model_data["model"], st.session_state.event_log["event_log"])

                    schedule_evaluation = client_gemini.models.generate_content(
                        model = os.getenv("GEMINI_MODEL"), 
                        contents = f""" 
                            Your goal is a realistic, lean, and minimal-bias estimation of the time (unit: days) needed to deploy a redesigned business process.
                            Input data:
                            1. General informatin about the type of business process: {schedule_evaluation_research.text}
                            2. Delta as-is and redesigned business process:
                                - As-is Activities: {st.session_state.event_log["tasks"]}
                                - Redesigned Activities: {bpmn_model_data["tasks"].keys()}
                                - As-is Variants: {st.session_state.event_log["process_variants"]}
                                - Redesigned Variants: {bpmn_model_data["process_variants"]}
                                - Change Intensity: {bpmn_model_data["degree_of_change"]} (Scale: 0.0 = no change, 1.0 = complete process replacement).
                            3. Contextual information about the company:
                                - Name: {st.session_state.contextual_data["name_of_organization"]}
                                - Size: {st.session_state.contextual_data["size"]}
                                - Experience with business process redesign projects: {st.session_state.contextual_data["experience_bpr"]}
                            Assumptions:
                            - Conceptual redesign work is done: The BPMN model of the redesigned business process exists. Do NOT include time for designing or discovering the process.
                            - If the activity names do not explicitly imply significant technological changes, assume that no technical infrastructure work (zero software development, zero API changes, and zero new tool installations) is required. 
                            - Implementation Scope: Only estimate the following fixed phases: 
                                - Change Preparation & Implementation Planning
                                - Training & Stakeholder Engagement (Scale duration based on Change Intensity)
                                - Pilot Implementation & Refinement (Scale duration based on Change Intensity)
                                - Go-Live & Monitoring
                            - Impact logic: A high 'Change Intensity' must primarily increase the duration of the 'Training & Stakeholder Engagement' and 'Pilot Implementation & Refinement' phases, while it has low/zero effects on 'Change Preparation & Implementation Planning' and 'Go-Live & Monitoring'
                            Estimation Bias:
                                - Apply a passive estimation bias. Prefer a lean, conservative duration (aim for the lower end of realistic) rather than over-estimating days
                            Provide a realistic duration based on the actual delta of the business processes (primary source).
                            General information about the type of business process and organizational info serve only as context.
                            """,
                        config = types.GenerateContentConfig(
                            system_instruction=system_prompts["schedule_evaluation"],
                            temperature=0.0,
                            response_mime_type="application/json",
                            response_schema=Schedule
                        )
                    )

                    res_parsed = schedule_evaluation.parsed
                    st.session_state.bpmn_models[bpmn_model_name]["metrics"]["Organizational Dimension"]["Schedule Feasability"]["Implementation Time"] = res_parsed.total_days
                    st.session_state.bpmn_models[bpmn_model_name]["ai_explanation"]["Implementation Time"] = {item.phase: {"time": item.days_for_phase, "activities": item.activities} for item in res_parsed.schedule_plan}

                    client_gemini.files.delete(name=bpmn_model_upload_ai.name)

    elif st.session_state.step == 3:

        with upload_columns[3]:
            st.divider()
            
        st.subheader(entry_stages[3])
        st.markdown("Now it's time to pairwise weight the importance of the different evaluation criteria. Please use the following scale to express how important one criterion is compared to another criterion for the evaluation of the redesigned business process alternatives.")
        
        ahp_scale = pd.DataFrame({
            "Value": ["1/9", "1/7", "1/5", "1/3", "1", "3", "5", "7", "9"],
            "Meaning": [
                "Criterion A is extremely less important than Criterion B",
                "Criterion A is very strongly less important than Criterion B",
                "Criterion A is strongly less important than Criterion B",
                "Criterion A is moderately less important than Criterion B",
                "Criterion A is equally important as Criterion B",
                "Criterion A is moderately more important than Criterion B",
                "Criterion A is strongly more important than Criterion B",
                "Criterion A is very strongly more important than Criterion B",
                "Criterion A is extremely more important than Criterion B"
            ]
        })

        with st.expander("Weighting scale", expanded=True):
            st.dataframe(ahp_scale, hide_index=True)

        criteria_pairwise_comparisons = {}

        with st.expander("Pairwise weight the importance of the criteria below", expanded=True):
            
            with st.form("criteria_comparison_form"):

                for main_criteria, sub_criteria in evaluation_metrics.items():
                    st.markdown(f"**{main_criteria}**")

                    if main_criteria == "Process Model Dimension":
                        st.info("Semantic Quality is evaluated by an LLM. Therefore, if semantic quality is given greater weight, the proportion of the LLM also increases.", icon="ℹ️")

                    if main_criteria == "Organizational Dimension":
                        st.info("Learning and Growth and Implementation Feasability are both evaluated by an LLM. Therefore, the propotion of the LLM is independent of your weights", icon="ℹ️")

                    sub_keys = list(sub_criteria.keys())
                    criteria_pairwise_comparisons[main_criteria] = {}

                    for k1, k2 in combinations(sub_keys, 2):

                        key_name = f"{main_criteria}_{k1}_{k2}"

                        criteria_pairwise_comparisons[main_criteria][(k1, k2)] = st.radio(
                            f"How important is **{k1}** compared to **{k2}**?",
                            ahp_scale["Value"],
                            index=4,
                            key=key_name,
                            horizontal=True
                        )
                    st.divider()
                        
                if st.form_submit_button("Start the Evaluation", use_container_width=True, icon="⚙️"):
                    st.session_state.criteria_pairwise_comparisons = criteria_pairwise_comparisons
                    st.session_state.evaluation_results = run_ahp_evaluation(evaluation_metrics, st.session_state.criteria_pairwise_comparisons, extract_metrics_from_dicts([st.session_state.bpmn_models, st.session_state.event_log]))
                    st.rerun()

    # Navigation buttons
    st.divider()
    upload_navigation_columns = st.columns(3)

    with upload_navigation_columns[0]:
        if st.button("Delete all uploaded data and start a new session", icon="🔄", use_container_width=True):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    # Disabling logic for the next-button
    disabled_step_event_log = (st.session_state.step == 0) and (st.session_state.event_log is None)
    disabled_step_bpmn_models = (st.session_state.step == 1) and (st.session_state.bpmn_models == {} or not st.session_state.submitted_new_tasks_gateways)
    disabled_step_context = (st.session_state.step == 2) and not st.session_state.contextual_data["form_submitted"]

    with upload_navigation_columns[2]:
        if st.session_state.step < 3:
            st.button(
                "Next step",
                icon="➡️",
                icon_position="right",
                on_click=next_step,
                disabled=disabled_step_event_log or disabled_step_bpmn_models or disabled_step_context,
                use_container_width=True
            )

else:
    st.success("The evaluation was successful. You can view the evaluation results in the 'Evaluation Results' tab or start a new evaluation by clicking the refresh button in your browser.", icon="✅")