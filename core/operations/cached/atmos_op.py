from core import OPERATIONS
from core.operations import CachedOp
from core.operations import ATMOSCORR_OP

@OPERATIONS.reg(name=ATMOSCORR_OP)
class AtmosCorr(CachedOp):
    def __init__(self, config:str):
        super().__init__(ATMOSCORR_OP)

    def __call__(self, *args):
        prev_result = args[0]
        x = prev_result[0]
        prev_att = prev_result[1]

        x = x + 1
        att = self.post_process(**prev_att)
        return x, att