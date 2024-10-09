from typing import TYPE_CHECKING
from core import OPERATIONS

from core.operations import TOPSAR_DEBURST_OP
from core.operations.parent import ParamOp, SnappyOp
from core.util import assert_bnames, ProductType
from core.util.op import call_constraint, op_constraint, OP_Module_Type
from core.raster import Raster, ModuleType
from core.util.snap import get_polarization, topsar_deburst

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=TOPSAR_DEBURST_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP])
class TopsarDeburst(ParamOp, SnappyOp):
    def __init__(self, polarisations:list[str]=None):
        super().__init__(TOPSAR_DEBURST_OP)

        self.add_param(selectedPolarisations=polarisations)

    @call_constraint(module_types=[ModuleType.SNAP], product_types=[ProductType.S1], ext=['safe'])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.get_param('selectedPolarisations'):
            self.add_param(selectedPolarisations= pols)
        else:
            assert_bnames(self.get_param('selectedPolarisations'), pols, 'Selected polarizations not found in metadata')

        raster.raw = topsar_deburst(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster