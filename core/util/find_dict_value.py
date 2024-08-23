from jsonpath_ng.ext import parse

def query_dict(jsonpath_pattern:str, target_dict:dict) -> list:
    return [match.value for match in parse(jsonpath_pattern).find(target_dict)]