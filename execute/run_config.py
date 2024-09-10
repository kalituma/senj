from argparse import ArgumentParser

from core import SCHEMA_PATH
from core.config import load_schema_map
from core.util import read_yaml
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder

def parse_args():
    parser = ArgumentParser(description="main script for preprocessing sentinel-1 and sentinel-2")
    parser.add_argument('--config_path', help="yaml based config file path")
    parser.add_argument('--log_dir', default='./log', help="log directory path")
    parser.add_argument('--log_level', default='info', help="log level")
    args = parser.parse_args()
    return args

def main(args):
    config_path = args.config_path
    schema_map = load_schema_map(SCHEMA_PATH)
    out_path = []
    with Context(GraphManager(read_yaml(config_path), schema_map)) as ctx:
        processor_builder = ProcessorBuilder(ctx)
        end_points = processor_builder.build()
        gens = [end_point.execute() for end_point in end_points]
        for gen in gens:
            for x in gen:
                out_path.append(x)

if __name__ == '__main__':
    args = parse_args()
    main(args)