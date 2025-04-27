import yaml
from core.util.logger import Logger

def read_yaml(config_path:str) -> dict:
    with open(config_path, 'r') as f:
        Logger.get_logger().log('debug', f'Reading config file: {config_path}')
        return yaml.safe_load(f)

def load_yaml(config:str)-> dict:
    Logger.get_logger().log('debug', f'Loading yaml config from text')
    return yaml.safe_load(config)

def read_yaml_text(config_path:str) -> str:
    with open(config_path, 'r') as f:
        Logger.get_logger().log('debug', f'Reading config file as text: {config_path}')
        data = yaml.safe_load(f)
        return yaml.dump(data, default_flow_style=False)