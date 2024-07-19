from core import PROCESSOR, OPERATIONS

class ProcessorBuilder:
    def __init__(self):
        self._processor = None
        self._linked_process = []
        self._operations = []

    @property
    def processor(self):
        return self._processor

    @processor.setter
    def processor(self, value):
        self._processor = value

    def make_processor(self, proc_type, proc_name, **kwargs):
        creator = PROCESSOR.get(proc_type)
        self._processor = creator(proc_name, **kwargs)
        return self

    def add_operations(self, ops:list, args_list:list):
        for op_name, args in zip(ops, args_list):
            self.add_operation(op_name, args)
        return self

    def add_operation(self, op_name, args):
        creator = OPERATIONS.get(op_name)
        self._operations.append(creator(**args))
        return self

    def add_linked_process(self, child_proc):
        self._linked_process.append(child_proc)
        return self

    def build(self):
        for op in self._operations:
            self._processor.add_op(op)
        for linked_proc in self._linked_process:
            self._processor.add_linked_process(linked_proc)
        return self._processor
