# Importing third-party libraries
import pm4py

# TODO: Check if it makes sense to split WF-net into its three criteria and handle these seperately
def check_bpmn_model_is_workflow_net(bpmn_model: pm4py.BPMN) -> bool:
    """
    Converts a BPMN model into a petri net and checks if it is a workflow net
    """
    pn, im, fm = pm4py.convert_to_petri_net(bpmn_model)
    return pm4py.check_is_workflow_net(pn)

# TODO: Check if it makes sense to split soundness into its three criteria and handle these seperately
def check_bpmn_model_for_soundness(bpmn_model: pm4py.BPMN) -> bool:
    """
    Converts a BPMN model into a petri net and checks it for soundness
    """
    pn, im, fm = pm4py.convert_to_petri_net(bpmn_model)
    return pm4py.check_soundness(pn, im, fm)[0]

def calculate_number_of_nodes(bpmn_model: pm4py.BPMN) -> int:
    """
    Calculates the total number of nodes (Tasks, Subprocesses, Events, Gateways) in the BPMN model
    """
    return len([node for node in bpmn_model.get_nodes() if isinstance(node, (pm4py.BPMN.Activity, pm4py.BPMN.Event, pm4py.BPMN.Gateway))])

def calculate_average_gateway_degree(bpmn_model: pm4py.BPMN) -> float:
    """
    Calculates the average degree (sum of in-arcs and out-arcs) of all gateways in the BPMN model
    """
    gateways = [node for node in bpmn_model.get_nodes() if isinstance(node, pm4py.BPMN.Gateway)]
    number_of_gateways = len(gateways)

    if number_of_gateways == 0:
        return 0.0

    total_gateway_degree = sum(len(gateway.get_in_arcs()) + len(gateway.get_out_arcs()) for gateway in gateways)
    
    return total_gateway_degree / number_of_gateways

def calculate_density(bpmn_model: pm4py.BPMN) -> float:
    """
    Calculates the structural density of a BPMN model as the ratio of actual sequence flows 
    to the maximum possible number of connections between all nodes
    """
    number_of_nodes = calculate_number_of_nodes(bpmn_model)
    number_of_arcs = len([flow for flow in bpmn_model.get_flows() if isinstance(flow, pm4py.BPMN.SequenceFlow)])

    return number_of_arcs / (number_of_nodes * (number_of_nodes - 1))

def calculate_sequentiality(bpmn_model: pm4py.BPMN) -> float:
    """
    Calculates the ratio of sequence flows in the BPMN model that connect two non-gateway elements
    """
    flows = bpmn_model.get_flows()
    
    counter = 0
    for flow in flows:
        source = flow.get_source()
        target = flow.get_target()

        source_is_gateway = isinstance(source, pm4py.BPMN.Gateway)
        target_is_gateway = isinstance(target, pm4py.BPMN.Gateway)

        if not source_is_gateway and not target_is_gateway:
            counter += 1

    return counter/len(flows)