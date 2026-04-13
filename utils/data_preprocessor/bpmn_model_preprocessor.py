import pm4py

def set_gateway_directions(bpmn_model: pm4py.BPMN) -> None:
    """
    Sets the gateway directions for all Gateways in the BPMN model according to the BPMN 2.0 specification
    """
    for node in bpmn_model.get_nodes():
        if isinstance(node, pm4py.BPMN.Gateway):
            if len(node.get_in_arcs()) == 1 and len(node.get_out_arcs()) > 1:
                node.set_gateway_direction("Diverging")
            elif len(node.get_in_arcs()) > 1 and len(node.get_out_arcs()) == 1:
                node.set_gateway_direction("Converging")
            else:
                node.set_gateway_direction("Unspecified")