from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import Op, CALIBRATE_OP
from core.util import assert_bnames, ProductType
from core.util.op import op_constraint, OP_TYPE
from core.raster import RasterType
from core.util.op import  call_constraint
from core.raster import Raster
from core.util.snap import calibrate, get_polarization

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=CALIBRATE_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.SNAP])
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

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
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

