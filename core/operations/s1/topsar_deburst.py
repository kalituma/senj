from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import Op, TOPSAR_DEBURST_OP
from core.util import assert_bnames, ProductType
from core.util.op import allow_product_type, allow_module_type
from core.raster import Raster, RasterType
from core.util.snap import get_polarization, topsar_deburst

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=TOPSAR_DEBURST_OP, conf_no_arg_allowed=True)
class TopsarDeburst(Op):
    def __init__(self, selectedPolarisations:list[str]=None):
        super().__init__(TOPSAR_DEBURST_OP)

        self.topsar_deburst_params = {
            'selectedPolarisations': selectedPolarisations
        }

    @allow_module_type(RasterType.SNAP)
    @allow_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.topsar_deburst_params['selectedPolarisations']:
            self.topsar_deburst_params['selectedPolarisations'] = pols
        else:
            assert_bnames(self.topsar_deburst_params['selectedPolarisations'], pols, 'Selected polarizations not found in metadata')

        raster.raw = topsar_deburst(raster.raw, self.topsar_deburst_params)
        raster = self.post_process(raster, context)
        return raster