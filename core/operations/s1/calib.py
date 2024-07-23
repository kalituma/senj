from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import Op, CALIBRATE_OP
from core.util import assert_bnames
from core.raster import ProductType, RasterType
from core.util import check_product_type, check_module_type
from core.raster import Raster
from core.raster.gpf_module import calibrate, get_polarization

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=CALIBRATE_OP)
class Calibrate(Op):
    def __init__(self, selectedPolarisations:list[str]=None, outputSigmaBand=True, outputBetaBand:bool=False, outputGammaBand:bool=False,
                 outputImageScaleInDb=False, outputImageInComplex:bool=False):
        
        super().__init__(CALIBRATE_OP)

        self.calib_params = {
            'selectedPolarisations': selectedPolarisations,
            'outputSigmaBand': outputSigmaBand,
            'outputGammaBand': outputGammaBand,
            'outputBetaBand': outputBetaBand,
            'outputImageInComplex': outputImageInComplex,
            'outputImageScaleInDb': outputImageScaleInDb
        }

    @check_module_type(RasterType.SNAP)
    @check_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.calib_params['selectedPolarisations']:
            self.calib_params['selectedPolarisations'] = pols
        else:
            assert_bnames(self.calib_params['selectedPolarisations'], pols, 'Selected polarizations not found in metadata')

        raster.raw = calibrate(raster.raw, self.calib_params)
        raster = self.post_process(raster, context)
        return raster

