from typing import TYPE_CHECKING
from core.util.gdal import warp_gdal
from core.operations.parent import ChainableOp

if TYPE_CHECKING:
    from core.logic.context import Context


class WarpOp(ChainableOp):
    def __init__(self, op_name):
        super().__init__(op_name)

    def call_warp(self, dataset, cur_params, context:"Context"):

        if self.init_flag:
            context.set('warp_params', cur_params)
        else:
            prev_params = context.get('warp_params')
            cur_params.update(prev_params)
            context.set('warp_params', cur_params)

        if self.end_flag:
            merged_params = context.get('warp_params')
            context.delete('warp_params')
            dataset = warp_gdal(dataset, merged_params)

        return dataset, context