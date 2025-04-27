from typing import Dict, Any, TYPE_CHECKING, Optional
from osgeo import osr

from core import OPERATIONS
from core.util.gdal import is_epsg_code_valid
from core.util.op import op_constraint, OP_Module_Type, PROJECTION_OP
from core.operations.parent import Op

if TYPE_CHECKING:
    from core.logic.context import Context
    from core.raster import Raster

def process_epsg(epsg:int):
    is_epsg_code_valid(epsg)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    return srs, epsg

def process_projection(proj_config):    
    srs = osr.SpatialReference()
    validate_projection_config(proj_config)
    
    srs.SetProjCS(proj_config.get('proj_cs'))
    srs.SetWellKnownGeogCS(proj_config.get('geog_cs', 'WGS84'))
    srs.SetLCC(
        proj_config.get('std_parallel1'),
        proj_config.get('std_parallel2'),
        proj_config.get('latitude_origin'),
        proj_config.get('longitude_origin'),
        proj_config.get('false_easting'),
        proj_config.get('false_northing')
    )
    epsg_code = srs.GetAuthorityCode(None)    
    return srs, epsg_code

def validate_projection_config(proj_config):
    
    proj_params_keys = ['proj_cs', 'geog_cs', 'std_parallel1', 'std_parallel2',
                        'latitude_origin', 'longitude_origin', 'false_easting', 'false_northing']
    
    proj_type = proj_config.get('proj_cs')
    assert proj_type in ['lcc'], 'Only Lambert Conformal Conic is supported'        
    
    for key in proj_params_keys:
        assert proj_config.get(key) is not None, f'{key} is required for Projection'

def process_gt(gt_config):
    validate_gt_config(gt_config)
    return [
        gt_config.get('ul_x'),
        gt_config.get('pixel_size_x'),
        0,
        gt_config.get('ul_y'),
        0,
        gt_config.get('pixel_size_y')
    ]

def validate_gt_config(gt_config):
    gt_params_keys = ['ul_x', 'ul_y', 'pixel_size_x', 'pixel_size_y']
    for key in gt_params_keys:
        assert gt_config.get(key) is not None, f'{key} is required for Geotransform'

@OPERATIONS.reg(name=PROJECTION_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL])
class Projection(Op):
    def __init__(self, epsg:Optional[int]=None, proj_params:Optional[Dict[str, Any]]=None, gt_params:Optional[Dict]=None, *args, **kwargs):
        super().__init__(PROJECTION_OP)        
        self.epsg = epsg
        self.proj_config = proj_params
        self.gt_config = gt_params

        self.srs = None
        self.epsg = None

        if epsg is not None:
            assert proj_params is None, 'One of epsg or projection should be provided'
        if proj_params is not None:
            assert epsg is None, 'One of epsg or projection should be provided'

        if epsg is None:
            assert proj_params is not None, 'Either epsg or projection should be provided'
        if proj_params is None:
            assert epsg is not None, 'Either epsg or projection should be provided'
        
        if epsg is not None:
            self.srs, self.epsg = process_epsg(epsg)
        else:
            self.srs, self.epsg = process_projection(self.proj_config)

        if self.gt_config is not None:
            self.gt = process_gt(self.gt_config)

    def __call__(self, raster:"Raster", context:"Context", *args, **kwargs) -> "Raster":        
        
        if self.srs is not None:
            raster.raw.SetProjection(self.srs.ExportToWkt())
        if self.gt is not None:            
            raster.raw.SetGeoTransform(self.gt)        
        
        raster = self.post_process(raster, context)
        return raster