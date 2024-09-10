from typing import Callable, Union, TYPE_CHECKING, AnyStr, List
from pathlib import Path

from core.operations import READ_OP
from core import PROCESSOR
from core.util.logger import print_log_attrs
from core.util.op import check_init_operation, MODULE_TYPE
from core.logic import FILE_PROCESSOR
from core.logic.processor import Processor, ProcessorType
from core.raster import Raster

@PROCESSOR.reg(FILE_PROCESSOR)
class FileProcessor(Processor):

    def __init__(self, proc_name:str, path:List, pattern:str='*', sort:dict=None, splittable:bool=True):
        super().__init__(proc_name=proc_name, proc_type=ProcessorType.FILE, splittable=splittable)
        self.roots:List = path
        self.search_pattern:str = pattern
        self.sort_func: Union[Callable, None] = None

        if sort is not None:
            self.sort_func:Callable = sort['func']

        # print_log_attrs(self, 'debug')

    def preprocess(self):
        if len(self.roots) == 0:
            raise AssertionError('No root path provided')

        if len(self.roots) == 1:
            root = self.roots[0]
            yield from self.get_file(root)

        elif len(self.roots) > 1:
            for root in self.roots:
                yield from self.get_file(root)


    def get_file(self, root:str):
        target_path = Path(root)
        ext = target_path.suffix[1:].lower()

        if target_path.is_file() or ext == 'safe':
            assert Path(root).exists(), f'File does not exist: {root}'
            yield root
        else:
            assert Path(root).exists(), f'File does not exist: {root}'
            p = Path(root).rglob(self.search_pattern)

            if self.sort_func is None:
                p_list = sorted(p)
            else:
                p_list = sorted(p, key=self.sort_func)

            if len(p_list) == 0:
                raise AssertionError(f'No file found with pattern: {self.search_pattern}')

            for x in p_list:
                if x.is_file() or x.suffix.lower() == '.safe':
                    yield str(x)

    @check_init_operation(READ_OP)
    def add_op(self, op):
        return super().add_op(op)

    def postprocess(self, x:Union[Raster, AnyStr], result_clone:bool=False):
        if isinstance(x, Raster):
            x = super().postprocess(x)
        return x

    def get_first_op_type(self) -> MODULE_TYPE:
        return self.ops[0].module_type

    def set_all_op_types(self):
        return self.apply_module_type_to_ops(self.get_first_op_type())