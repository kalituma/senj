from typing import TYPE_CHECKING

from core import PROCESSOR
from core.logic import LINK_PROCESSOR
from core.logic.processor import Processor

if TYPE_CHECKING:
    from core.logic.executor import ProcessingExecutor

@PROCESSOR.reg(LINK_PROCESSOR)
class LinkProcessor(Processor):
    def __init__(self, proc_name:str='', processors:list[Processor]=None, splittable:bool=False):
        super().__init__(proc_name=proc_name, splittable=splittable)
        if processors is None:
            self.proc_list = []
        else:
            self.proc_list = processors

    def add_linked_process(self, linked_proc:Processor):
        self.proc_list.append(linked_proc)
        return self

    def preprocess(self):

        if len(self.proc_list) == 1:
            gens = self.proc_list[0].execute()
        else:
            gens = [single_executor.execute() for single_executor in self.proc_list]

        while True:
            try:
                if len(self.proc_list) == 1:
                    yield from gens
                else:
                    yield [next(gen) for gen in gens]
            except StopIteration as e:
                break

    def postprocess(self, x, result_clone:bool=False):
        return x

    def set_executor(self, executor:"ProcessingExecutor"):

        super().set_executor(executor)

        for single_process in self.proc_list:
            if isinstance(single_process, Processor):
                single_process.set_executor(executor)

    def __contains__(self, proc):
        return proc in self.proc_list