from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import CALIBRATE_OP
from core.operations.parent import ParamOp, SnappyOp
from core.util import assert_bnames, ProductType

from core.util.op import op_constraint, OP_TYPE, call_constraint
from core.util.snap import calibrate, get_polarization
from core.raster import Raster, RasterType
from core.raster.funcs import create_meta_dict, init_bname_index_in_meta, set_raw_metadict

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=CALIBRATE_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.SNAP])
class Calibrate(ParamOp, SnappyOp):

    def __init__(self, selectedPolarisations:list[str]=None, outputSigmaBand=True, outputBetaBand:bool=False, outputGammaBand:bool=False,
                 outputImageScaleInDb=False, outputImageInComplex:bool=False):
        
        super().__init__(CALIBRATE_OP)
        self.add_param(selectedPolarisations=selectedPolarisations,
                       outputSigmaBand=outputSigmaBand,
                       outputBetaBand=outputBetaBand,
                       outputGammaBand=outputGammaBand,
                       outputImageScaleInDb=outputImageScaleInDb,
                       outputImageInComplex=outputImageInComplex)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1], ext=['safe'])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.get_param('selectedPolarisations'):
            self.add_param(selectedPolarisations=pols)
        else:
            assert_bnames(self.get_param('selectedPolarisations'), pols, 'Selected polarizations not found in metadata')

        raster.raw = calibrate(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster

