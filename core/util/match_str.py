from fnmatch import fnmatch

def is_contained(target_list:list, src_list:list):
    return all([t in src_list for t in target_list])

def glob_match(str_list:list[str], pattern:str):
    return [s for s in str_list if fnmatch(s, pattern)]