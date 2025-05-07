
from abc import ABC
from pathlib import Path
from core.util import ModuleType
from core.raster import Raster

from core.util.snap import (
    find_proj_from_band, 
    create_product, 
    add_band_to_product, 
    find_gt_from_band, 
    find_geocoding_from_wkt
)

from core.util.gdal import create_ds_with_dict
from core.util.nc import get_proj_nc
from core.raster.funcs import read_band_from_raw
from core.raster.funcs.meta import MetaBandsManager

class FormatConverter(ABC):
    @classmethod    
    def convert(cls, raster: Raster, target_type: ModuleType):
        source_type = raster.module_type
        
        if source_type == target_type:
            return raster
        
        converter_key = (source_type, target_type)
        if converter_key not in cls._converter_map:
            raise ValueError(f"No converter found for {source_type} to {target_type}")
        
        if not raster.is_band_cached:
            raster = read_band_from_raw(raster, selected_name_or_id=None)

        raster = cls._converter_map[converter_key](raster)
        raster.del_bands_cache()

        return raster
    
    @classmethod
    def _convert_gdal_to_snap(cls, raster: Raster):

        cached_bands = raster.bands

        product_name = Path(raster.path).stem
        if product_name == '':
            product_name = 'converted_product'
        width, height = raster.raw.RasterXSize, raster.raw.RasterYSize
        product = create_product(product_name, file_format='dim', width=width, height=height)
        geocoding = find_geocoding_from_wkt(raster.raw.GetProjection(), raster.raw.GetGeoTransform(),
                                            raster.raw.RasterXSize, raster.raw.RasterYSize)
        product.setSceneGeoCoding(geocoding)
        product = add_band_to_product(product, cached_bands)
        raster.raw = product
        raster.module_type = ModuleType.SNAP
        
        return raster
    
    @classmethod
    def _convert_snap_to_gdal(cls, raster: Raster):
        cached_bands = raster.bands
        assert raster.cached_bands_have_same_shape(), 'All converted bands should have the same shape'

        band_name_list = list(cached_bands.keys())
                
        wkt = find_proj_from_band(raster.raw.getBand(band_name_list[0]))
        gt = find_gt_from_band(raster.raw.getBand(band_name_list[0]))
        
        raster.raw, btoi = create_ds_with_dict(cached_bands, gdal_format='MEM', proj_wkt=wkt, transform=gt, metadata=None, out_path='')
        raster.module_type = ModuleType.GDAL
        
        if btoi != raster.band_to_index:
            MetaBandsManager(raster).update_band_mapping(btoi)

        return raster

    @classmethod
    def _convert_netcdf_to_gdal(cls, raster: Raster):
        cached_bands = raster.bands
        assert raster.cached_bands_have_same_shape(), 'All converted bands should have the same shape'

        band_name_list = list(cached_bands.keys())

        wkt, gt = get_proj_nc(raster.path, band_name_list[0])
        raster.raw, btoi = create_ds_with_dict(cached_bands, gdal_format='MEM', proj_wkt=wkt, transform=gt,metadata=None, out_path='')
        raster.module_type = ModuleType.GDAL

        if btoi != raster.band_to_index:
            MetaBandsManager(raster).update_band_mapping(btoi)

        return raster

FormatConverter._converter_map = {
    (ModuleType.GDAL, ModuleType.SNAP): FormatConverter._convert_gdal_to_snap,
    (ModuleType.SNAP, ModuleType.GDAL): FormatConverter._convert_snap_to_gdal,
    (ModuleType.NETCDF, ModuleType.GDAL): FormatConverter._convert_netcdf_to_gdal,
}
    
    