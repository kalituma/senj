import json
from core.util.logger import Logger

def read_json(json_path:str):
    with open(json_path, 'r') as file :
        Logger.get_logger().log('debug', f'Reading json file: {json_path}')
        json_dict = json.load(file)
    return json_dict