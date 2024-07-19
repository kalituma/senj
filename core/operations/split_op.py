import numpy as np

from core.operations import Op
from core.operations import OPERATIONS, SPLIT_OP

@OPERATIONS.reg(name=SPLIT_OP)
class Split(Op):
    def __init__(self, axis:int):
        super().__init__(SPLIT_OP)
        self.axis = axis

    def __call__(self, *args):
        prev_result = args[0]
        assert isinstance(prev_result[0], np.ndarray), 'SplitOp requires a numpy array'

        arr = prev_result[0]
        att = prev_result[1]
        arr = np.split(arr, arr.shape[self.axis], axis=self.axis)
        new_atts = self.post_process(**att)
        result = [(arr_, dict(new_atts)) for arr_ in arr]
        return result