class NullValueError(Exception):
    def __init__(self, key):
        self.key = key
        super().__init__(f"Null value for key '{key}'")

def check_null_error(cerberus_error:dict) -> bool:
    for key, value in cerberus_error.items():
        for elem in value:
            if isinstance(elem, str):
                if 'null value' in elem:
                    return True
    return False