import pm4py
import xml.etree.ElementTree as ET

def get_bpmn_tasks(bpmn_model: pm4py.BPMN) -> list:
    """
    Returns a list with the names of all taks in the BPMN model
    """
    return [node.get_name() for node in bpmn_model.get_nodes() if isinstance(node, pm4py.BPMN.Task)]

def get_xor_or_gateways_with_multiple_outgoing_flows(bpmn_model: pm4py.BPMN) -> dict:
    """
    Returns a dictionary with all XOR and OR Gateways with multiple outgoing sequence flows in the BPMN model with their corresponding outgoing sequence flows
    """
    xor_or_gateways_with_outgoing_flows = {}
    for flow in bpmn_model.get_flows():
        if isinstance(flow, pm4py.BPMN.SequenceFlow):
            source = flow.get_source()
            if isinstance(source, (pm4py.BPMN.ExclusiveGateway, pm4py.BPMN.InclusiveGateway)):
                if len(source.get_out_arcs()) > 1:
                    key = source
                    value = flow.get_target().get_name()
                    xor_or_gateways_with_outgoing_flows.setdefault(key, []).append(value)

    return xor_or_gateways_with_outgoing_flows

def get_bpmn_resources(file_path: str) -> list:
    """
    Returns a list with all resources in the BPMN model (based on lanes)
    """
    bpmn_model = ET.parse(file_path)
    root = bpmn_model.getroot()

    resources = []

    for elem in root.iter():
        if elem.tag.endswith("lane") and elem.get("name"):
            resources.append(elem.get("name"))
    
    return resources