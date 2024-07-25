import numpy as np

def compare_nested_dicts_with_arrays(dict1, dict2):

    if type(dict1) != type(dict2):
        return False

    if isinstance(dict1, dict):
        if set(dict1.keys()) != set(dict2.keys()):
            return False
        return all(compare_nested_dicts_with_arrays(dict1[key], dict2[key]) for key in dict1)

    elif isinstance(dict1, (list, tuple)):
        if len(dict1) != len(dict2):
            return False
        return all(compare_nested_dicts_with_arrays(v1, v2) for v1, v2 in zip(dict1, dict2))

    elif isinstance(dict1, np.ndarray):
        return np.array_equal(dict1, dict2, equal_nan=True)

    else:
        return dict1 == dict2