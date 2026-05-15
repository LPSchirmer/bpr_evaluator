# Importing third-party libraries
import ahpy
import itertools

# Definition of cost criteria (lower values are better)
cost_criteria = { 
    "Number of violated Completeness Requirements", 
    "Number of Nodes", 
    "Average Gateway Degree", 
    "Density", 
    "Mean cycle time", 
    "Mean process costs", 
    "Repeatability",
    "Number of Legal Issues", 
    "Implementation Time"
}

def parse_fraction(value: str) -> float:
    """
    Parses a string that may represent a fraction (e.g. "1/3") into a float. If the string does not contain a fraction, it is converted directly to a float
    """
    value = str(value).strip()
    if "/" in value:
        x, y = value.split("/")
        return float(x) / float(y)
    
    return float(value)

def equal_weight_comparisons(names: list) -> dict:
    """
    Generates a dictionary of pairwise comparisons with equal weights (1) for all pairs of names
    """
    if len(names) == 1:
        return {(names[0], names[0]): 1}
    
    return {pair: 1 for pair in itertools.combinations(names, 2)}

def normalize(values: dict, is_cost: bool = False) -> tuple:
    """
    Implements linear sum normalization
    """
    raw_data = values.copy()
    if not values:
        return {}, {}

    normalized_results = {}

    eps = 1e-9 # Minimal offset to prevent division through 0
    
    if is_cost:

        reciprocals = {
            alt: (1.0 / (val if val > 0 else eps)) 
            for alt, val in values.items()
        }

        sum_reciprocals = sum(reciprocals.values())
        
        if sum_reciprocals == 0:
            return {k: 0.0 for k in values}, raw_data
            
        for alt, recip in reciprocals.items():
            normalized_results[alt] = recip / sum_reciprocals

    else:

        total_sum = sum(values.values())
        
        if total_sum == 0:
            return {k: 1.0/len(values) for k in values}, raw_data
            
        for alt, r_ij in values.items():
            normalized_results[alt] = r_ij / total_sum

    return normalized_results, raw_data

def get_node_metrics(node_subtree: dict, alternatives_metrics: dict) -> dict:
    """
    Normalizes metrics via linear sum normalization and returns the metrics in raw and normalized form
    """
    metrics_report = {}
    leaves = [k for k, v in node_subtree.items() if v is None]
    
    for metric in leaves:
        is_cost = metric in cost_criteria
        raw_vals = {alt: m[metric] for alt, m in alternatives_metrics.items() if metric in m}
        
        if not raw_vals:
            continue
            
        norm_vals, raw_vals = normalize(raw_vals, is_cost=is_cost)
        
        metrics_report[metric] = {
            alt: {"raw": raw_vals[alt], "normalized": norm_vals[alt]}
            for alt in raw_vals
        }

    return metrics_report

def build_subtree(node_name: str, node_subtree: dict, alternatives_metrics: dict, comparisons: dict | None = None) -> ahpy.Compare:
    """
    Constructs AHP compare hierarchy for a given dimension
    """
    def process(name: str, children: dict, comps: dict | None) -> ahpy.Compare:
        """
        Constructs AHP compare objects inside a given dimension
        """
        leaves = [k for k, v in children.items() if v is None]
        non_leaves = [k for k, v in children.items() if v is not None]
        child_objs = []
        
        for metric in leaves:
            is_cost = metric in cost_criteria
            raw = {alt: m[metric] for alt, m in alternatives_metrics.items() if metric in m}
            norm, _ = normalize(raw, is_cost=is_cost) if raw else ({a: 1.0/len(alternatives_metrics) for a in alternatives_metrics}, {})
            child_objs.append(ahpy.Compare(name=metric, comparisons=norm, precision=4))
            
        for cn in non_leaves:
            child_objs.append(process(cn, children[cn], None))
            
        node_comps = comps if comps is not None else equal_weight_comparisons(leaves + non_leaves)
        node_obj = ahpy.Compare(name=name, comparisons=node_comps, precision=4)
        node_obj.add_children(child_objs)

        return node_obj

    return process(node_name, node_subtree, comparisons)

def traverse(node_name: str, node_subtree: dict, alternatives_metrics: dict, view_dict: dict, comparisons: dict | None = None) -> None:
    """
    Adds target weights, local weights, consistency ratio, and metric details to a given dimension
    """
    isolated = build_subtree(node_name, node_subtree, alternatives_metrics, comparisons)
    metric_details = get_node_metrics(node_subtree, alternatives_metrics)
    
    view_dict[node_name] = {
        "target_weights": isolated.target_weights,
        "local_weights": isolated.local_weights,
        "consistency_ratio": isolated.consistency_ratio,
    }
    
    if metric_details:
        view_dict[node_name]["metrics_data"] = metric_details

    for child_name, child_subtree in node_subtree.items():
        if isinstance(child_subtree, dict):
            traverse(child_name, child_subtree, alternatives_metrics, view_dict)

def run_ahp_evaluation(hierarchy: dict, view_comparisons: dict, alternatives_metrics: dict) -> dict:
    """
    Runs the AHP Evaluation and returns its results in a dict containing the target weights, local weights, consistency ratios, and metric details for all dimensions
    """
    results = {}
    for view_name in hierarchy.keys():
        view_subtree = hierarchy[view_name]
        view_results = {}
        parsed_top_comps = {k: parse_fraction(v) for k, v in view_comparisons.get(view_name, {}).items()}
        
        traverse(view_name, view_subtree, alternatives_metrics, view_results, parsed_top_comps)
        results[view_name] = view_results

    return results