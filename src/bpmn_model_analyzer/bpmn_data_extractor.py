import pm4py

def get_bpmn_tasks(bpmn_model: pm4py.BPMN) -> dict:
    """
    Returns a dictionary with the id's (keys) and names (values) of all tasks in the BPMN model
    """
    return {node.get_id(): node.get_name() for node in bpmn_model.get_nodes() if isinstance(node, pm4py.BPMN.Task)}

def is_task(node: pm4py.BPMN.BPMNNode) -> bool:
    """
    Checks if a BPMN node is a task
    """
    return isinstance(node, pm4py.BPMN.Task)

def get_first_target_tasks_from_gateway(flow: pm4py.BPMN.Flow, visited = None) -> set:
    """
    Returns the first target tasks that are reached from a given gateway flow
    """
    if visited is None: 
        visited = set()

    target = flow.get_target()

    if target in visited: 
        return set()
    
    visited.add(target)

    if is_task(target):
        return {target.get_name()}

    tasks = set()
    for out_flow in target.get_out_arcs():
        tasks.update(get_first_target_tasks_from_gateway(out_flow, visited))

    return tasks

def get_xor_split_gateway_target_tasks(bpmn_model: pm4py.BPMN) -> dict:
    """
    Returns a dictionary with the id's of the gateways (XOR Split) as keys and a nested dictionary with the outgoing flows and the list with its first target tasks as values
    """
    gateways = {}
    for node in bpmn_model.get_nodes():
        if isinstance(node, pm4py.BPMN.ExclusiveGateway):
            out_arcs = node.get_out_arcs()

            if len(out_arcs) > 1:
                gateways[node.get_id()] = {}

                for flow in out_arcs:

                    path_id = flow.get_id()
                    tasks = list(get_first_target_tasks_from_gateway(flow))
                    gateways[node.get_id()][path_id] = tasks

    return gateways