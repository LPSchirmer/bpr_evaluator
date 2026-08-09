# Importing third-party libraries
import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import math

# Setting project root directory to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing custom src modules
from src.process_evaluator.process_metrics_calculator import *
from src.process_evaluator.ahp_engine import cost_criteria

# Importing custom utils modules
from utils.file_processor.created_file_processor import *
from utils.file_processor.uploaded_file_processor import *

# Page metadata
icon = "⚙️"
title = "Evaluation Results"
st.set_page_config(page_title=title, page_icon=icon, layout="wide")

# Start of page content
st.title(f"{icon} {title}")

if st.session_state.evaluation_results:

    # Introduction general data
    with st.container(border=True):
        columns = st.columns(3)
        with columns[0]:
            st.markdown(f"Organization: :gray-badge[{st.session_state.contextual_data["name_of_organization"]}]", text_alignment="center")
        with columns[1]:
            st.markdown(f"Process: :gray-badge[{st.session_state.contextual_data["name_of_process"]}]", text_alignment="center")
        with columns[2]:
            st.markdown(f"As-is process: :gray-badge[{st.session_state.event_log["event_log_name"]}]", text_alignment="center")

        redesigned_badges = ", ".join(f":gray-badge[{alternative}]" for alternative in st.session_state.bpmn_models.keys())
        st.markdown(f"Redesigned business process alternatives: {redesigned_badges}", text_alignment="center")

    st.markdown("To correctly interpret the results, please consider the following note: ")
    st.info("All values, except for the raw metric values in the detailed metric analysis and simulation deviation section, are normalized on a standardized scale to enable a uniform comparison. This scale ranges from 0 (worst) to 1 (best), so higher values indicate better results. In addition, the sum of all rated alternatives within a single hierarchy level is always equal to the value of its parent criterion, reflecting their absoulte distribution.", icon="ℹ️")

    st.header("Global Dimension Evaluation")

    with st.container(border=True):
        
        categories = list(evaluation_metrics.keys())
        first_view_name = categories[0]
        alternatives = list(st.session_state.evaluation_results[first_view_name][first_view_name]["target_weights"].keys())

        fig_spider = go.Figure()

        max_value = 0

        for alt in alternatives:
            values = []

            for view in categories:
                score = st.session_state.evaluation_results[view][view]["target_weights"].get(alt, 0)
                values.append(score)

                if score > max_value:
                    max_value = score

            values.append(values[0])

            formatted_categories = [category.replace(" ", "<br>") for category in categories]

            fig_spider.add_trace(go.Scatterpolar(
                r=values,
                theta=formatted_categories + [formatted_categories[0]],
                fill='none',
                name=alt,
                hovertemplate=f"<b>{alt}</b><br>%{{theta}}<br>Score: %{{r:.4f}}<extra></extra>"
            ))

        fig_spider.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max_value],
                    tickfont=dict(
                        size=14,
                        color="black"
                    )
                ),
                angularaxis=dict(
                    tickfont=dict(
                        size=16,
                        color="black",
                        family="Times New Roman"
                    )
                )
            ),
            showlegend=True,
            legend_title="Business Process Alternatives",
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig_spider)
        
        st.divider()
        
        rank_cols = st.columns(len(categories))

        for i, view in enumerate(categories):
            with rank_cols[i]:
                with st.container(border=True):
                    st.markdown(f"**{view}**")
                    
                    view_node = st.session_state.evaluation_results[view][view]

                    sorted_alts = sorted(alternatives, key=lambda x: view_node["target_weights"][x], reverse=True)
                    
                    current_rank = 0
                    last_score = -1

                    for idx, alt in enumerate(sorted_alts, 1):
                        score = view_node["target_weights"][alt]
                        
                        if round(score, 4) != round(last_score, 4):
                            current_rank = idx
                        
                        last_score = score
                        
                        medal = "🥇" if current_rank == 1 else "🥈" if current_rank == 2 else "🥉" if current_rank == 3 else f"{current_rank}."
                        
                        st.write(f"{medal} **{alt}** ({score:.4f})")

        with st.expander("View the BPMN models"):

            file_path_as_is_vis = create_path_for_created_visualizations(st.session_state.visualizations_folder_path, st.session_state.event_log["event_log_name"])
            pm4py.save_vis_bpmn(st.session_state.event_log["inductive_bpmn_model"], file_path_as_is_vis)
            st.image(file_path_as_is_vis, caption=f"BPMN visualization of {st.session_state.event_log['event_log_name']} (as-is process)", width="stretch")

            for index, (name, data) in enumerate(st.session_state.bpmn_models.items()):
                file_path_to_be_vis = create_path_for_created_visualizations(st.session_state.visualizations_folder_path, name)
                pm4py.save_vis_bpmn(data["model"], file_path_to_be_vis)
                st.image(file_path_to_be_vis, caption=f"BPMN visualization of {name}", width="stretch")

    st.header("Detailed Evaluation by Dimension")

    for view_name in evaluation_metrics.keys():

        with st.container(border=True):
            st.subheader(view_name)
            
            tab_visual, tab_data = st.tabs(["📊 Visualized Summary", "📋 Detailed Data Representation"])

            view_results = st.session_state.evaluation_results[view_name]
            main_node = view_results[view_name]
            alternatives = list(main_node["target_weights"].keys())
            criteria_weights = main_node["local_weights"]
            
            with tab_visual:
                fig = go.Figure()
                for crit_name, weight in criteria_weights.items():
                    scores = [weight * view_results[crit_name]["target_weights"][alt] for alt in alternatives]
                    fig.add_trace(go.Bar(name=crit_name, x=alternatives, y=scores, text=[f"{score:.4f}" for score in scores], textposition='auto'))
                
                fig.update_layout(barmode='stack', margin=dict(l=10, r=10, t=10, b=10),
                                xaxis_title="Alternative", yaxis_title="Normalized Value", hovermode="x unified", legend_title="Criteria")
                
                st.plotly_chart(fig)

            with tab_data:
                table_data = []
                
                sorted_alts = sorted(alternatives, key=lambda x: main_node["target_weights"][x], reverse=True)
                
                current_rank = 0
                last_score = -1

                for idx, alt in enumerate(sorted_alts, 1):
                    score = main_node["target_weights"][alt]

                    if round(score, 4) != round(last_score, 4):
                        current_rank = idx
                    last_score = score
                    
                    medal = "🥇" if current_rank == 1 else "🥈" if current_rank == 2 else "🥉" if current_rank == 3 else f"{current_rank}."

                    row = {
                        "Ranking": medal,
                        "Alternative": alt,
                        "Overall Score": round(score, 4)
                    }
                    
                    for crit_name, weight in criteria_weights.items():
                        weighted_contribution = weight * view_results[crit_name]["target_weights"][alt]
                        row[f"{crit_name} (weighted with {weight})"] = round(weighted_contribution, 4)
                    
                    table_data.append(row)
                
                df_results = pd.DataFrame(table_data)
                
                st.dataframe(
                    df_results, 
                    hide_index=True,
                    column_config={
                        "Overall Score": st.column_config.NumberColumn(format="%.4f"),
                        "Ranking": st.column_config.TextColumn(help="Rank based on the overall score")
                    }
                )

                with st.expander("Detailed Metric Analysis"):
                
                    tab_norm, tab_raw = st.tabs(["⚖️ Normalized Metric Values", "🔢 Raw Metric Values"])

                    top_level_criteria = criteria_weights.keys()

                    def render_metrics_representation(mode="raw"):
                        """
                        Detailed metrics expander in raw and normalized form
                        """
                        for parent_crit in top_level_criteria:
                            relevant_sub_groups = {}
                            
                            if "metrics_data" in view_results.get(parent_crit, {}):
                                relevant_sub_groups[parent_crit] = view_results[parent_crit]["metrics_data"]
                            
                            if "local_weights" in view_results.get(parent_crit, {}):
                                for child_crit in view_results[parent_crit]["local_weights"].keys():
                                    if child_crit in view_results and "metrics_data" in view_results[child_crit]:
                                        relevant_sub_groups[child_crit] = view_results[child_crit]["metrics_data"]

                            if relevant_sub_groups:
                                with st.expander(parent_crit, expanded=True):
                                    for group_name, metrics in relevant_sub_groups.items():
                                        st.markdown(f"#### {group_name}")
                                        
                                        for m_name, m_values in metrics.items():
                                            cost_benefit_icon = "➖" if m_name in cost_criteria else "➕"
                                            unit_scale_note = f"(Unit/scale: {evaluation_metrics_description[m_name]["unit"]})"
                                            st.markdown(f"{cost_benefit_icon if mode=="raw" else ""} **{m_name}** {unit_scale_note if mode=="raw" else ""}", help=evaluation_metrics_description[m_name]["description"])
                                            cols = st.columns(len(alternatives))
                                            as_is_key = f"{st.session_state.event_log['event_log_name']} (adjusted as-is process)"

                                            base_score_dict = m_values.get(as_is_key, {})
                                            base_val = base_score_dict.get("raw") if mode == "raw" else base_score_dict.get("normalized")

                                            for i, alt_name in enumerate(alternatives):
                                                score_dict = m_values.get(alt_name, {})
                                                current_val = score_dict.get("raw") if mode == "raw" else score_dict.get("normalized")
                                                
                                                delta_str = None
                                                delta_color = "normal"
                                                delta_arrow = "auto"

                                                if mode == "raw" and alt_name != as_is_key and base_val is not None and base_val != 0:
                                                    diff_pct = ((current_val - base_val) / abs(base_val)) * 100
                                                    
                                                    if round(diff_pct, 2) == 0:
                                                        delta_str = "0.00%"
                                                        delta_color = "off"
                                                        delta_arrow = "off"
                                                    else:
                                                        delta_str = f"{diff_pct:.2f}%"
                                                        
                                                        is_cost = m_name in cost_criteria

                                                        if is_cost:
                                                            delta_color = "inverse"
                                                        else:
                                                            delta_color = "normal"

                                                with cols[i]:
                                                    def render_explanation(criteria_dict, m_name):
                                                        """
                                                        AI explanation for metrics that are evaluated by AI
                                                        """
                                                        if not criteria_dict:
                                                            return
                                                            
                                                        for crit, eval_text in criteria_dict.items():
                                                            if m_name == "Number of violated Compliance Requirements":
                                                                st.markdown(f"Violated rule: :red['{crit}']")

                                                            else:
                                                                st.markdown(f"Violated criteria: :red['{crit}']")

                                                            st.markdown("**Explanation:**")   
                                                            st.markdown(f"* {eval_text}")  
                                                            st.divider()

                                                    ai_explanation_criteria = st.session_state.event_log.get("ai_explanation", {}).keys()

                                                    if m_name in ai_explanation_criteria:

                                                        if m_name == "Required Implementation Time":
                                                            
                                                            if "adjusted as-is process" in alt_name:
                                                                st.info("As this business process is already implemented, its required implementation time is obviously always equal to 0.", icon="ℹ️")
                                                                
                                                            else:
                                                                with st.expander("View AI Explanation", icon="🤖"):
                                                                    bp_data = st.session_state.bpmn_models.get(alt_name, {})
                                                                    ai_explanations = bp_data.get("ai_explanation", {})
                                                                    target_data = ai_explanations.get(m_name, {})

                                                                    for i, (phase_name, phase_data) in enumerate(target_data.items()):
                                                                        st.markdown(f"{i+1}. {phase_name} ({phase_data["time"]} days)")
                                                                        st.markdown(f"* {phase_data["activities"]}")
                                                                        st.divider()

                                                        else:

                                                            with st.expander("View AI Explanation", icon="🤖"):
                                                                
                                                                if "adjusted as-is process" in alt_name:
                                                                    as_is_eval = st.session_state.event_log.get("ai_explanation", {})
                                                                    target_data = as_is_eval.get(m_name, {})
                                                                    render_explanation(target_data, m_name)
                                                                    
                                                                else:
                                                                    bp_data = st.session_state.bpmn_models.get(alt_name, {})
                                                                    ai_explanations = bp_data.get("ai_explanation", {})
                                                                    target_data = ai_explanations.get(m_name, {})
                                                                    render_explanation(target_data, m_name)

                                                    display_val = f"{current_val:.4f}" if isinstance(current_val, float) else str(current_val)

                                                    if math.modf(current_val)[0] == 0:
                                                        display_val = str(int(current_val))

                                                    st.metric(
                                                        label=alt_name, 
                                                        value=display_val, 
                                                        delta=delta_str,
                                                        delta_color=delta_color,
                                                        delta_arrow=delta_arrow,
                                                        delta_description="compared to adjusted as-is process" if delta_str else None
                                                    )
    
                                        st.divider()

                    with tab_norm:
                        render_metrics_representation(mode="norm")

                    with tab_raw:
                        st.info("The values in this tab represent raw data rather than standardized scores. For clarity: cost criteria (lower is better) are marked with ➖, while benefit criteria (higher is better) are indicated by ➕.", icon="ℹ️")
                        render_metrics_representation(mode="raw")

            with st.expander("How reliable are the results?", expanded=True):

                st.metric(label = f"Conistency Ratio for {view_name}", 
                            value = view_results[view_name]["consistency_ratio"], 
                            delta = "Your judgements are consistent" if view_results[view_name]["consistency_ratio"] <= 0.10 else "Your judgements are inconsistent",
                            delta_color = "green" if view_results[view_name]["consistency_ratio"] <= 0.10 else "red",
                            delta_arrow="off",
                            help = "In the Analytic Hierarchy Process, the Consistency Ratio is a measure used to validate the reliability of your pairwise criteria comparisons by checking how consistent your judgements are. It tells your if your logic is coherent (e. g., if A > B and B > C, then A should be > C). Values <= 0.10 are generally considered acceptable, while higher values suggest you should re-evaluate your inputs.")
                
                if view_name == "Process Dimension":
                    st.divider()
                    st.markdown("Simulation Deviation", help="Since simulation is a probabilistic process, the as-is process is always simulated to check the difference between ground-truth and the simulated baseline. For alternative comparison, the mean value per metric between ground truth and simulation result is used.")
                    sim_columns = st.columns(len(st.session_state.event_log["metrics"]))
                    sim_columns_names = ["Ground Truth", "Simulated as-is process", "Adjusted as-is process"]
                    for i, (metric_name, metric_values) in enumerate(st.session_state.event_log["metrics"].items()):
                        with sim_columns[i]:
                            with st.container(border=True):
                                st.markdown(f"#### {sim_columns_names[i]}")
                                for x in metric_values["Process Dimension"]:
                                    for met_name, met_value in metric_values["Process Dimension"][x].items():
                                        st.metric(label=f"{met_name} (Unit/scale: {evaluation_metrics_description[met_name]['unit']})", 
                                                  value=f"{met_value:.4f}", 
                                                  help=evaluation_metrics_description[met_name]["description"])

else:
    st.warning("There are no evaluation results available. Start in the tab 'Start Evaluation' by uploading the necessary data.", icon="⚠️")

# TODO: Interactive visualizations of BPMN models
# TODO: Check if rounding methodology is consistent