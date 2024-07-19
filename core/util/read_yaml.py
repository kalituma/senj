import yaml

def read_yaml(config_path:str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)