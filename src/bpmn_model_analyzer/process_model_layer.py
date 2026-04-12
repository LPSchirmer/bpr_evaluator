import pm4py

def check_for_ingoing_and_outgoing_activity_sequence_flows(bpmn_model: pm4py.BPMN) -> int:
    """
    Checks if all activities in the BPMN model have at least one ingoing and one outgoing sequence flow. Returns the number of activities that are faulty in that sense
    """
    faulty_tasks = []

    for node in bpmn_model.get_nodes():
        if isinstance(node, pm4py.BPMN.Task):
            if not node.get_in_arcs() or not node.get_out_arcs():
                faulty_tasks.append(node)

    return len(faulty_tasks)

def check_for_ingoing_start_event_sequence_flows(bpmn_model: pm4py.BPMN) -> int:
    """
    Checks if all start events in the BPMN model have no ingoing sequence flows. Returns the number of start events that are faulty in that sense
    """
    faulty_start_events = []

    for node in bpmn_model.get_nodes():
        if isinstance(node, pm4py.BPMN.StartEvent):
            if node.get_in_arcs():
                faulty_start_events.append(node)

    return len(faulty_start_events)

# TODO: Check if it makes sense to split soundness into the three criteria and handle these seperately
def check_bpmn_model_for_soundness(bpmn_model: pm4py.BPMN) -> bool:
    """
    Converts a BPMN model in a petri net and checks it for soundness
    """
    pn, im, fm = pm4py.convert_to_petri_net(bpmn_model)
    return pm4py.check_soundness(pn, im, fm)[0]