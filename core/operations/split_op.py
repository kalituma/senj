from typing import TYPE_CHECKING

import numpy as np

from core.operations import Op
from core.operations import OPERATIONS, SPLIT_OP
from core.raster.funcs import split_raster

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=SPLIT_OP)
class Split(Op):
    def __init__(self, axis:int=0, bands:list=None):
        super().__init__(SPLIT_OP)
        self.axis = axis
        self.bands = bands

    def __call__(self, raster:"Raster", context:"Context", *args) -> list["Raster"]:

        results = split_raster(raster, self.bands)

        for res in results:
            res.op_history.append(self.name)

        return results