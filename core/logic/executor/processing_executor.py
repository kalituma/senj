from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.logic import Context
    from core.logic.processor import Processor

class ProcessingExecutor:
    def __init__(self, context:"Context"):
        self.context = context

    def execute(self, processor:"Processor"):
        for i, data in enumerate(processor.preprocess()):

            if processor.splittable:
                # processor_id = id(processor)
                # if processor_id not in self.context.counter:
                #     self.context.counter[processor_id] = 1
                # else:
                #     self.context.counter[processor_id] += 1

                # if processor_id in self.context.cache:
                #     copied = copy_raster(self.context.cache[processor_id])
                #     yield copied
                # else:
                x = processor.process(data, self.context)
                x = processor.postprocess(x)
                # self.context._cache[processor_id] = x
                yield x

            else:
                x = processor.process(data, self.context)
                x = processor.postprocess(x)
                yield x

    def reset_cache(self):
        self.context._cache.clear()
        self.execution_count = 0