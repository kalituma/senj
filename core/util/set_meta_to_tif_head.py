from osgeo import gdal

def set_btoi_to_tif(tif_path, band_name_to_index:dict[str, int]):
    ds = gdal.Open(tif_path, gdal.GA_Update)
    return set_btoi_to_tif_meta(ds, band_name_to_index)

def set_btoi_to_tif_meta(ds, band_name_to_index:dict[str, int]):

    ds.SetMetadata({}, 'band_to_index')
    for bname, b_idx in band_name_to_index.items():
        ds.SetMetadataItem(bname, f'{b_idx}', 'band_to_index')
    ds.FlushCache()
    return ds

def get_btoi_from_tif(tif_path):
    ds = gdal.Open(tif_path)
    return get_btoi_to_tif_meta(ds)

def get_btoi_to_tif_meta(ds):
    band_to_index = ds.GetMetadata('band_to_index')
    if len(band_to_index) == 0:
        band_to_index = None
    return band_to_index