def get_dict_leaves(dictionary: dict):
    """
    Recursively finds the root/leaves in a nested dictionary and returns its key and value
    """
    for key, value in dictionary.items():
        if isinstance(value, dict):
            yield from get_dict_leaves(value)
        else:
            yield key, value