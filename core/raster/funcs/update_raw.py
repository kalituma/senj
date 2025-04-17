from core.util import assert_bnames, remove_list_elements
from core.util.gdal import read_gdal_bands_as_dict, create_ds_with_dict
from core.util.snap import copy_cached_to_raw_gpf, read_gpf_bands_as_dict, del_bands_from_product
from core.raster import Raster, ModuleType
from core.raster.funcs.meta import MetaDictManager
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

    if module_type == ModuleType.SNAP:
        updated_bands = read_gpf_bands_as_dict(raster_obj.raw, selected_bands)
        for bname in selected_bands:
            raster_obj.bands[bname] = updated_bands[bname]

    elif module_type == ModuleType.GDAL:
        updated_bands = read_gdal_bands_as_dict(raster_obj.raw, selected_bands)
        for bname in selected_bands:
            raster_obj.bands[bname] = updated_bands[bname]

    else:
        raise NotImplementedError(f'Raster type {module_type} is not implemented')

    return raster_obj

def update_raw_from_cache(raster:Raster, clear=False):
    # raw to cache
    if raster.is_band_cached:
        cached_bands = raster.get_cached_band_names()

        module_type = raster.module_type

        if module_type == ModuleType.SNAP:
            if clear:
                raster.raw = del_bands_from_product(raster.raw, raster.get_band_names())
            else:
                raster.raw = del_bands_from_product(raster.raw, cached_bands)

            raster.raw = copy_cached_to_raw_gpf(raster.raw, cached_band=raster.bands)

            if raster.get_band_names() != list(raster.raw.getBandNames()):
                raster.update_band_map_to_meta(list(raster.raw.getBandNames()))
                raster.copy_band_map_from_meta()

        elif module_type == ModuleType.GDAL:

            not_cached_bands = remove_list_elements(raster.get_band_names(), remove_list=cached_bands)
            added_cached_bands = remove_list_elements(cached_bands, remove_list=raster.get_band_names())

            assert raster.cached_bands_have_same_shape(), 'All selected bands should have the same shape'

            if not clear:
                if len(not_cached_bands) > 0:
                    raster = read_band_from_raw(raster, selected_name_or_id=not_cached_bands, add_to_cache=True)

            raster.convert_to_have_same_dtype()
            cached_order = raster.get_band_names() + added_cached_bands
            raster.reorder_bands(cached_order)

            proj = raster.raw.GetProjection()
            gt = raster.raw.GetGeoTransform()
            metadata = raster.raw.GetMetadata()
            raster.raw = None
            raster.raw, btoi = create_ds_with_dict(raster.bands, 'MEM', proj_wkt=proj, transform=gt, metadata=metadata, out_path='')
            if btoi != raster.band_to_index:
                MetaDictManager(raster).update_band_mapping(btoi)
        else:
            raise NotImplementedError(f'Raster type {module_type} is not implemented')

    raster.del_bands_cache()

    return raster