import numpy as np

from core import OPERATIONS

from core.logic import Context
from core.util import ProductType
from core.util.op import REV_REF_OP, op_constraint, OP_Module_Type, call_constraint
from core.raster import Raster
from core.operations.parent import CachedOp, SelectOp

@OPERATIONS.reg(name=REV_REF_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP, OP_Module_Type.GDAL])
class RevRef(CachedOp):
    def __init__(self):
        super().__init__(REV_REF_OP)

    @call_constraint(product_types=[ProductType.S2])
    def __call__(self, raster:Raster, context:Context, *args, **kwargs):

        assert 'atmos_band_meta' in raster.meta_dict, 'this operation requires atmos_band_meta in the raster meta_dict'

        all_bands = raster.get_band_names()
        self.log(f'target band to recover dn number from reflectance : {all_bands}')
        cached_raster = self.pre_process(raster, context, bands_to_load=all_bands)

        QUANTIFICATION_VALUE = 10000
        for key, band in cached_raster.bands.items():
            assert np.isnan(band['no_data']), 'no_data should be np.nan'
            radio_offset = raster.meta_dict['atmos_band_meta'][key]['radio_offset']
            band['value'] = (band['value'] * QUANTIFICATION_VALUE) + np.abs(radio_offset)
            band['value'][np.isnan(band['value'])] = 0
            band['value'] = band['value'].astype(np.uint16)
            band['no_data'] = 0

        self.post_process(cached_raster, context, clear=True)

        return raster