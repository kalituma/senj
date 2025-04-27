# todo: should have process_file function and it should be executed by multiprocessing

from typing import TYPE_CHECKING, Type, Union, AnyStr, List
from multiprocessing import Pool, cpu_count

from core import PROCESSOR
from core.logic import MULTI_PROCESSOR
from core.logic.processor import Processor, ProcessorType
from core.raster import Raster

if TYPE_CHECKING:
    from core.logic.context import Context
    from core.logic.executor import ProcessingExecutor

@PROCESSOR.reg(MULTI_PROCESSOR)
class MultiProcessor(Processor):
    def __init__(self, proc_name:str='', batch_size:int=4, num_workers:int=None, splittable:bool=True):
        super().__init__(proc_name=proc_name, proc_type=ProcessorType.SUB, splittable=splittable)
        self.batch_size = batch_size
        self.num_workers = num_workers if num_workers is not None else max(1, cpu_count() - 1)
        self.file_paths = []
        
    def preprocess(self):        
        for file_path in self.collect_file_paths():
            self.file_paths.append(file_path)
            
        batches = [self.file_paths[i:i + self.batch_size] 
                  for i in range(0, len(self.file_paths), self.batch_size)]
        
        for batch in batches:
            with Pool(processes=self.num_workers) as pool:
                results = pool.map(self.process_file, batch)
            
            for result in results:
                yield result
    
    def collect_file_paths(self):            
        pass
    
    def process_file(self, file_path:str) -> Raster:        
        from core.logic import Context
        ctx = Context(None) 
        
        raster = Raster(file_path)
        
        return self.process(raster, ctx)
        
    def postprocess(self, x:Union[Raster, AnyStr]):
        if isinstance(x, Raster):
            x = super().postprocess(x)
        return x