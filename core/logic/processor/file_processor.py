from typing import Callable, Union
from pathlib import Path

from core import PROCESSOR
from core.logic import FILE_PROCESSOR
from core.logic.processor import Processor

@PROCESSOR.reg(FILE_PROCESSOR)
class FileProcessor(Processor):

    def __init__(self, proc_name:str, path:str, pattern:str='*', sort:dict=None, splittable:bool=True):
        super().__init__(proc_name=proc_name, splittable=splittable)
        self.root:str = path
        self.search_pattern:str = pattern
        self.sort_func: Union[Callable, None] = None

        if sort is not None:
            self.sort_func:Callable = sort['func']

    def preprocess(self):
        target_path = Path(self.root)
        ext = target_path.suffix[1:]

        if target_path.is_file() or ext == 'SAFE':
            assert Path(self.root).exists(), f'File does not exist: {self.root}'
            yield self.root
        else:
            p = Path(self.root).rglob(self.search_pattern)
            if self.sort_func is None:
                p_list = sorted(p)
            else:
                p_list = sorted(p, key=self.sort_func)

            for x in p_list:
                if x.is_file():
                    yield str(x)

    def postprocess(self, x, result_clone:bool=False):
        return x