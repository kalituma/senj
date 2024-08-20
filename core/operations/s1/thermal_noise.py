from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import Op, THERM_NOISE_OP
from core.util import op_product_type, check_module_type, ProductType
from core.util import assert_bnames
from core.raster import Raster, RasterType
from core.raster.gpf_module import get_polarization, thermal_noise_removal

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=THERM_NOISE_OP)
class ThermalNoiseRemoval(Op):
    def __init__(self, selectedPolarisations:list[str]=None):
        super().__init__(THERM_NOISE_OP)
        self.therm_noise_params = {
            'selectedPolarisations': selectedPolarisations
        }

    @check_module_type(RasterType.SNAP)
    @op_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.therm_noise_params['selectedPolarisations']:
            self.therm_noise_params['selectedPolarisations'] = pols
        else:
            assert_bnames(self.therm_noise_params['selectedPolarisations'], pols, 'Selected polarizations not found in metadata')

        raster.raw = thermal_noise_removal(raster.raw, self.therm_noise_params)
        raster = self.post_process(raster)
        return raster