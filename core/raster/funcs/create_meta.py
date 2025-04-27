from typing import Union, TYPE_CHECKING, Optional, List, Dict, Any
from pathlib import Path
from core.util import ProductType, read_pickle, parse_meta_xml, load_gdal, deprecated

from core.raster import ModuleType
from core.util.parse_meta_text import parse_meta_capella
from core.util.gdal import get_image_spec_gdal, get_geo_spec_gdal
from core.util.snap import make_meta_dict_from_product, get_image_spec_gpf, get_geo_spec_gpf
from core.util.nc import make_meta_dict_from_nc_ds

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from esa_snappy import Product

def _get_specs(raw: Union["Dataset", "Product"], module_type: ModuleType) -> tuple:
    if module_type == ModuleType.GDAL:
        image_spec = get_image_spec_gdal(raw)
        geo_spec = get_geo_spec_gdal(raw)
    else:
        image_spec = get_image_spec_gpf(raw)
        geo_spec = get_geo_spec_gpf(raw)
    
    return image_spec, geo_spec

def _update_tile_info(tile_info: Dict[str, Any], image_spec: Dict[str, Any], geo_spec: Dict[str, Any]) -> Dict[str, Any]:
    for corner in ['ul', 'ur', 'lr', 'll']:
        tile_info[f'{corner.upper()}COLOFFSET'] = image_spec[f'{corner}_col']
        tile_info[f'{corner.upper()}ROWOFFSET'] = image_spec[f'{corner}_row']
    
    for corner in ['ul', 'ur', 'll', 'lr']:
        tile_info[f'{corner.upper()}X'] = tile_info[f'{corner.upper()}LON'] = geo_spec[f'{corner}_x']
        tile_info[f'{corner.upper()}Y'] = tile_info[f'{corner.upper()}LAT'] = geo_spec[f'{corner}_y']
    
    tile_info['FILENAME'] = ''
    return tile_info

def _update_band_info(band_info: Dict[str, Dict[str, Any]], geo_spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    for band in band_info.values():
        for corner in ['ul', 'ur', 'll', 'lr']:
            band[f'{corner.upper()}LON'] = geo_spec[f'{corner}_x']
            band[f'{corner.upper()}LAT'] = geo_spec[f'{corner}_y']
    
    return band_info

def update_meta_dict(meta_dict: Dict[str, Any], raw: Union["Dataset", "Product"], module_type: ModuleType) -> Dict[str, Any]:
    tmp_tile_info = meta_dict['TILE_INFO'][0].copy()
    tmp_band_info = meta_dict['BAND_INFO'].copy()
    
    image_spec, geo_spec = _get_specs(raw, module_type)
    
    tmp_tile_info = _update_tile_info(tmp_tile_info, image_spec, geo_spec)
    tmp_band_info = _update_band_info(tmp_band_info, geo_spec)
    
    meta_dict['OR_TILE_FILE_NAMES'] = [tile_info['FILENAME'] for tile_info in meta_dict['TILE_INFO']]
    meta_dict['TILE_INFO'] = [tmp_tile_info]
    meta_dict['BAND_INFO'] = tmp_band_info

    return meta_dict

@deprecated
def _try_load_cached_meta(raster_path: str) -> Optional[Dict[str, Any]]:
    if not raster_path:
        return None
        
    ext = Path(raster_path).suffix
    pkl_meta_path = raster_path.replace(ext, '.pkl')
    
    if Path(pkl_meta_path).exists():
        return read_pickle(pkl_meta_path)
    
    return None

@deprecated
def get_tif_dimension(raw: Union["Dataset", "Product", None], gdal) -> Optional[List[int]]:
    if raw is None:
        return None
        
    if isinstance(raw, gdal.Dataset):
        return [raw.RasterYSize, raw.RasterXSize]
    
    return None

@deprecated
def create_meta_dict(
    raw: Union["Product", "Dataset"], 
    product_type: ProductType, 
    module_type: ModuleType, 
    raster_path: str, 
    update_meta_bounds: bool
) -> Optional[Dict[str, Any]]:

    gdal = load_gdal()
    
    meta_dict = _try_load_cached_meta(raster_path)

    if meta_dict:
        return meta_dict
    
    if module_type == ModuleType.SNAP and (product_type in [ProductType.S2, ProductType.S1]):
        return make_meta_dict_from_product(raw, product_type)
    
    if module_type == ModuleType.NETCDF:
        return make_meta_dict_from_nc_ds(raw)
    
    if product_type == ProductType.CP:
        meta_path = raster_path.replace('.tif', '.json')
        extended_meta_path = raster_path.replace('.tif', '_extended.json')
        assert Path(meta_path).exists() and Path(extended_meta_path).exists(), f'meta file not found in {meta_path} and {extended_meta_path}'
        meta_dict = parse_meta_capella(meta_path, extended_meta_path)               
        return meta_dict        
    
    if product_type != ProductType.UNKNOWN:
        tif_file_dim = get_tif_dimension(raw, gdal)
        meta_dict = parse_meta_xml(raster_path, product_type, tif_file_dim)
        
        if update_meta_bounds and product_type == ProductType.WV:
            meta_dict = update_meta_dict(meta_dict, raw, module_type)
            
        return meta_dict
    
    return None
