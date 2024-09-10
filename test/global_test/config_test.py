from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder
from core.util import read_yaml

def executeGraph(config_path, schema_map):
    out_path = []

    with Context(GraphManager(read_yaml(config_path), schema_map)) as ctx:
        processor_builder = ProcessorBuilder(ctx)
        end_points = processor_builder.build()
        gens = [end_point.execute() for end_point in end_points]
        for gen in gens:
            for x in gen:
                out_path.append(x)

    return out_path