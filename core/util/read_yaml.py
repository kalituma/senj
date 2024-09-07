import yaml
from core.util.logger import Logger

def read_yaml(config_path:str) -> dict:
    with open(config_path, 'r') as f:
        Logger.get_logger().log('debug', f'Reading config file: {config_path}')
        return yaml.safe_load(f)