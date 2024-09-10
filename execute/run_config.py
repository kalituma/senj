from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime

from core import SCHEMA_PATH
from core.config import load_schema_map
from core.util import read_yaml, Logger, expand_var
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder

def parse_args():
    parser = ArgumentParser(description="main script for preprocessing sentinel-1 and sentinel-2")
    parser.add_argument('--config_path', help="yaml based config file path")
    parser.add_argument('--log_dir', default='$ROOT_DIR/OUTPUTDATA', help="log directory path")
    parser.add_argument('--log_level', default='info', help="log level")
    args = parser.parse_args()
    return args

def main(args):

    log_dir = expand_var(args.log_dir)
    assert Path(log_dir).exists(), f'Log directory({log_dir}) does not exist'

    config_name = Path(args.config_path).stem
    time_start = datetime.now()
    log_id = f"{config_name}_{time_start.strftime('%Y%m%d_%H%M%S')}"
    log_path = str(Path(log_dir) / f'{log_id}.log')
    Logger.get_logger(log_level=args.log_level, log_file_path=log_path)

    config_path = args.config_path
    assert Path(config_path).exists(), f'Config file({config_path}) does not exist'
    schema_map = load_schema_map(SCHEMA_PATH)

    out_path = []
    all_config = read_yaml(config_path)
    with Context(GraphManager(all_config, schema_map)) as ctx:
        processor_builder = ProcessorBuilder(ctx)
        end_points = processor_builder.build()
        gens = [end_point.execute() for end_point in end_points]
        for gen in gens:
            for x in gen:
                out_path.append(x)

if __name__ == '__main__':
    args = parse_args()
    main(args)