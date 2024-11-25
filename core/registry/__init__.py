from .registry import *

LAMBDA = Registry(name='lambda_func', package='core.lambda_funcs')
PROCESSOR = Registry(name='processor', package='core.logic.processor')
EXECUTOR = Registry(name='executor', package='core.logic.executor')
OPERATIONS = Registry(name='operations', package='core.operations')