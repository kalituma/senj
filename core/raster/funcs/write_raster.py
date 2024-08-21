from pathlib import Path
from core.raster import Raster, RasterType
from core.util.snap import write_gpf, write_metadata, is_bigtiff_gpf
from core.util.gdal import copy_ds, is_bigtiff_gdal
from core.raster.funcs import wrap_up_raster, update_cached_to_raw

def write_raster(raster:Raster, out_path:str, out_module:"RasterType"):
    # before execute this function, you should call warp-up function to update raw data

    selected_bands = raster.selected_bands

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    ext = Path(out_path).suffix[1:]

    raster = update_cached_to_raw(raster) # copy bands to raw
    raster = wrap_up_raster(raster, selected_bands=selected_bands, out_module=out_module)

    if raster.module_type == RasterType.GDAL:
        is_bigtiff = is_bigtiff_gdal(raster.raw)
        if is_bigtiff:
            compress = True
        else:
            compress = False

        if raster.meta_dict:
            write_metadata(raster.meta_dict, out_path)

        raster.raw = copy_ds(raster.raw, "GTiff", is_bigtiff=is_bigtiff, compress=compress, out_path=out_path)

    elif raster.module_type == RasterType.SNAP:
        if ext == 'dim':
            write_gpf(raster.raw, out_path, 'BEAM-DIMAP')
        elif ext == 'tif':
            is_bigtiff = is_bigtiff_gpf(product=raster.raw)
            if is_bigtiff:
                format_type = 'GeoTIFF-BigTIFF'
            else:
                format_type = 'GeoTIFF'

            if raster.meta_dict:
                write_metadata(raster.meta_dict, out_path)

            write_gpf(raster.raw, out_path, format_type)
        else:
            raise ValueError(f'Extension {ext} is not supported in SNAP module')
    else:
        raise NotImplementedError(f'Write function for {raster.module_type.__str__()} is not implemented')