from core.util import assert_bnames, remove_list_elements
from core.util.gdal import read_gdal_bands_as_dict, create_ds_with_dict
from core.util.snap import copy_cached_to_raw_gpf, read_gpf_bands_as_dict
from core.raster import Raster, RasterType
from core.raster.funcs import read_band_from_raw

def update_raster_from_raw(raster_obj:Raster, selected_bands=None):
    # cache to raw
    if raster_obj.bands is None:
        raster_obj.bands = {}

    if selected_bands is None:
        selected_bands = raster_obj.get_band_names()
    else:
        assert_bnames(selected_bands, raster_obj.get_band_names(), f'selected bands not found in raster{raster_obj.path}')

    module_type = raster_obj.module_type

    if module_type == RasterType.SNAP:
        updated_bands = read_gpf_bands_as_dict(raster_obj.raw, selected_bands)
        for bname in selected_bands:
            raster_obj.bands[bname] = updated_bands[bname]

    elif module_type == RasterType.GDAL:
        updated_bands = read_gdal_bands_as_dict(raster_obj.raw, selected_bands)
        for bname in selected_bands:
            raster_obj.bands[bname] = updated_bands[bname]

    else:
        raise NotImplementedError(f'Raster type {module_type} is not implemented')

    return raster_obj

def update_raw_from_cache(raster_obj:Raster):
    # raw to cache
    if raster_obj.is_band_cached:
        cached_bands = raster_obj.get_cached_band_names()
        not_cached_bands = remove_list_elements(raster_obj.get_band_names(), remove_list=cached_bands)

        module_type = raster_obj.module_type

        if module_type == RasterType.SNAP:
            raster_obj.raw = copy_cached_to_raw_gpf(raster_obj.raw, cached_band=raster_obj.bands)

        elif module_type == RasterType.GDAL:
            assert raster_obj.cached_bands_have_same_shape(), 'All selected bands should have the same shape'

            if len(not_cached_bands) > 0:
                raster_obj = read_band_from_raw(raster_obj, selected_name_or_id=not_cached_bands, add_to_cache=True)

            proj = raster_obj.raw.GetProjection()
            gt = raster_obj.raw.GetGeoTransform()
            metadata = raster_obj.raw.GetMetadata()
            raster_obj.raw = None
            raster_obj.raw = create_ds_with_dict(raster_obj.bands, 'MEM', proj_wkt=proj, transform=gt, metadata=metadata, out_path='')
        else:
            raise NotImplementedError(f'Raster type {module_type} is not implemented')

    raster_obj.del_bands_cache()

    return raster_obj