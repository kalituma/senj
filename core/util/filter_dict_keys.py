def filter_dict_keys(key_set, string_list):
    def is_match(value, string_list):
        key_parts = value.split('_')
        return any(s == part for part in key_parts for s in string_list)

    result = list()
    for value in key_set:
        if is_match(value, string_list):
            result.append(value)
    return result