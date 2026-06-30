# Importing third-party libraries
import pm4py
from pm4py.objects.random_variables.random_variable import RandomVariable
from pm4py.algo.simulation.montecarlo.utils.replay import get_map_from_log_and_net
from pm4py.algo.simulation.montecarlo.algorithm import apply as monte_carlo_simulation
import pandas as pd

def find_next_labeled_tasks_in_net(start_transition: pm4py.PetriNet.Transition, visited = None) -> set:
    """
    Returns the next labeled target transitions that are reached from a given gateway flow
    """
    if visited is None:
        visited = set()

    if start_transition in visited:
        return set()
    
    visited.add(start_transition)

    if start_transition.label is not None:
        return {start_transition.label}
    
    found_labels = set()

    for arc in start_transition.out_arcs:
        place = arc.target
        for next_arc in place.out_arcs:
            found_labels.update(find_next_labeled_tasks_in_net(next_arc.target, visited))

    return found_labels

def start_monte_carlo_simulation(bpmn_model: pm4py.BPMN, 
                                 bpmn_model_reference: pm4py.BPMN, 
                                 event_log: pd.DataFrame, 
                                 processing_times: dict, 
                                 new_xor_splits: dict, 
                                 num_process_instances: int, 
                                 arrival_time: float,
                                 number_of_resources: int) -> pd.DataFrame:
    """
    Performs a monte carlo simulation on a given BPMN model and returns the simulated event log in a df
    """
    # Stochastic map of as-is process
    ref_net, ref_initial_marking, ref_final_marking = pm4py.convert_to_petri_net(bpmn_model_reference)
    log_stochastic_map_ref = get_map_from_log_and_net(event_log, ref_net, ref_initial_marking, ref_final_marking)
    
    # Store all transitions of the stochastic map of as-is process that are not None in a seperate dict
    label_to_rv = {}
    for t, rv in log_stochastic_map_ref.items():
        if t.label:
            label_to_rv[t.label] = rv

    # Stochastic map of redesigned process
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)
    stochastic_map = get_map_from_log_and_net(event_log, net, initial_marking, final_marking)

    # If there is no intersection between the as-is process and the redesigned process, manually initialize stochastic map
    if stochastic_map == {}:
        for transition in net.transitions:
            if transition.label:
                stochastic_map[transition] = None

    def get_safe_rate(duration: float) -> float:
        """
        Returns the expected value of the duration of an activity for exponential distribution
        """
        return 1.0 / max(float(duration), 0.000001)
    
    # Task durations
    for transition in stochastic_map.keys():
        label = transition.label
        
        # Prio 1: Processing times that are set by the user
        if label in processing_times:
            new_rv = RandomVariable()
            new_rv.read_from_string("EXPONENTIAL", get_safe_rate(processing_times[label]))
            new_rv.set_weight(1.0)
            stochastic_map[transition] = new_rv

        # Prio 2: Processing times that are given by event log data
        elif label in label_to_rv:
            ref_rv = label_to_rv[label]
            stochastic_map[transition] = ref_rv
           
            if stochastic_map[transition].get_weight() is None:
                stochastic_map[transition].set_weight(1.0)

    # Gateway probabilities
    for g_id, task_weights in new_xor_splits.items():
        gateway_place = next((p for p in net.places if g_id in str(p.name)), None)
        
        if gateway_place:
            
            def get_decision_transitions(current_place: pm4py.PetriNet.Place, visited_places=None) -> list:
                """
                Finds the actual transitions following the decision place (Conversion from BPMN to Petri Net creates silent transitions)
                """
                if visited_places is None:
                    visited_places = set()

                if current_place in visited_places:
                    return []
                
                visited_places.add(current_place)
                
                transitions = []
                for arc in current_place.out_arcs:
                    t = arc.target

                    if t.label is None:
                        next_places = [a.target for a in t.out_arcs]

                        for np in next_places:

                            if len(np.out_arcs) > 1:
                                transitions.extend(get_decision_transitions(np, visited_places))

                            else:
                                transitions.append(t)
                    else:
                        transitions.append(t)

                return list(set(transitions))

            out_transitions = get_decision_transitions(gateway_place)
            
            for t in out_transitions:
                if t in stochastic_map:
                    stochastic_map[t].set_weight(0.000001)

            for t in out_transitions:
                reachable_labels = find_next_labeled_tasks_in_net(t)
                for label_name, weight in task_weights.items():
                    if label_name in reachable_labels:
                        if t in stochastic_map:
                            stochastic_map[t].set_weight(float(weight))

    # Specify simulation parameters
    parameters = {
        "num_simulations": int(num_process_instances),
        "case_arrival_ratio": float(arrival_time),
        "provided_stochastic_map": stochastic_map,
        "default_num_resources_per_place": number_of_resources
    }

    # Run Simulation with parameters
    simulated_log, _ = monte_carlo_simulation(event_log, net, initial_marking, final_marking, parameters=parameters)

    # Convert simulated event log dict into df
    rows = []
    for case_id, trace in enumerate(simulated_log):
        for event in trace:
            rows.append({
                "case:concept:name": f"sim_{case_id}",
                "concept:name": event["concept:name"],
                "time:timestamp": event["time:timestamp"]
            })

    return pd.DataFrame(rows)