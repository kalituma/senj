from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import CALIBRATE_OP
from core.operations.parent import ParamOp, SnappyOp
from core.util import assert_bnames, ProductType

from core.util.op import op_constraint, OP_Module_Type, call_constraint
from core.util.snap import calibrate, get_polarization
from core.raster import Raster, ModuleType
from core.raster.funcs import create_meta_dict, init_bname_index_in_meta, set_raw_metadict

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=CALIBRATE_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP])
class Calibrate(ParamOp, SnappyOp):

    def __init__(self, polarisations:list[str]=None, output_sigma=True, output_beta:bool=False, output_gamma:bool=False,
                 output_in_db=False, output_in_complex:bool=False):
        
        super().__init__(CALIBRATE_OP)
        self.add_param(selectedPolarisations=polarisations,
                       outputSigmaBand=output_sigma,
                       outputBetaBand=output_beta,
                       outputGammaBand=output_gamma,
                       outputImageScaleInDb=output_in_db,
                       outputImageInComplex=output_in_complex)

    @call_constraint(module_types=[ModuleType.SNAP], product_types=[ProductType.S1], ext=['safe'])
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

