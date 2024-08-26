from pathlib import Path
from core.raster import Raster, RasterType, EXT_MAP
from core.util.snap import write_gpf, write_metadata, is_bigtiff_gpf
from core.util.gdal import copy_ds, is_bigtiff_gdal
from core.util.errors import ExtensionNotSupportedError

def write_raster(raster:Raster, out_path:str):

    out_ext = Path(out_path).suffix[1:]

    if raster.module_type == RasterType.GDAL:
        is_bigtiff = is_bigtiff_gdal(raster.raw)
        if is_bigtiff:
            compress = True
        else:
            compress = False

        if raster.meta_dict:
            write_metadata(raster.meta_dict, out_path)
        raster.raw = copy_ds(raster.raw, "GTiff", is_bigtiff=is_bigtiff, compress=compress, out_path=out_path, band_to_index=raster._band_to_index)

    elif raster.module_type == RasterType.SNAP:
        if out_ext == 'dim':
            write_gpf(raster.raw, out_path, 'BEAM-DIMAP')
        elif out_ext == 'tif':
            is_bigtiff = is_bigtiff_gpf(product=raster.raw)
            if is_bigtiff:
                format_type = 'GeoTIFF-BigTIFF'
            else:
                format_type = 'GeoTIFF'
            if raster.meta_dict:
                write_metadata(raster.meta_dict, out_path)
            write_gpf(raster.raw, out_path, format_type)
        else:
            raise ExtensionNotSupportedError(module=raster.module_type, available_exts=EXT_MAP[raster.module_type.__str__()], specified_ext=out_ext)
    else:
        raise NotImplementedError(f'Write function for {raster.module_type.__str__()} is not implemented')