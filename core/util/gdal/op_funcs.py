from osgeo import gdal

def read_gdal(gtiff_path):

    ds = gdal.Open(gtiff_path)
    arr = ds.ReadAsArray()
    ch_count = ds.RasterCount
    arr = transpose_3d(arr, ch_count)

    return GeoTiff(gt_meta=ds.GetMetadata(), gt_proj=ds.GetProjection(), gt_arr=arr,
                   gt_transform=ds.GetGeoTransform(), gt_dataset=ds, gt_src_path=gtiff_path,
                   gt_tar_path=None, gt_ch_count=ch_count)

def stack_gdal(gtiffs, order:list=None, axis=0):
    if order is None:
        order = [0, 1, 2]

    gtiffs = [gtiffs[i] for i in order]

    # check if all inputs have the same shape and projection
    for i in range(1, len(gtiffs)):
        if not _check_info_equal(gtiffs[0], gtiffs[i]):
            raise ValueError(f"inputs must have the same shape and projection")

    stacked_arr = np.concatenate([x.gt_arr for x in gtiffs], axis=axis)

    return GeoTiff(gt_meta=gtiffs[0].gt_meta, gt_proj=gtiffs[0].gt_proj, gt_arr=stacked_arr,
                   gt_transform=gtiffs[0].gt_transform, gt_dataset=None, gt_ch_count=stacked_arr.shape[axis],
                   gt_src_path=gtiffs[0].gt_src_path, gt_tar_path=None)



# warp
def reprojection_gdal(gtiff, to_epsg:int):

    mem_ds = _create_mem_ds(gtiff)
    warp_options = _build_warp_option(from_epsg=int(wkt_to_epsg(gtiff.gt_proj)), to_epsg=to_epsg)
    out_ds = _wrap_gdal(mem_ds, warp_options)
    out_ds.FlushCache()
    gtiff.dataset = out_ds
    return gtiff

# warp
def subset_gdal(gtiff, bounds):

    mem_ds = _create_mem_ds(gtiff)
    warp_options = _build_warp_option(from_epsg=wkt_to_epsg(gtiff.gt_proj), bounds=bounds)
    out_ds = _wrap_gdal(mem_ds, warp_options)
    out_ds.FlushCache()
    gtiff.dataset = out_ds
    return gtiff

# warp
NEAREST = gdal.GRA_NearestNeighbour
BILINEAR = gdal.GRA_Bilinear
CUBIC = gdal.GRA_Cubic
CUBICSPLINE = gdal.GRA_CubicSpline
LANCZOS = gdal.GRA_Lanczos

def resample_gdal(gtiff, res:float, alg:str):

    mem_ds = _create_mem_ds(gtiff)
    warp_options = gdal.WarpOptions(format='MEM', xRes=res, yRes=res, resampleAlg=alg)
    out_ds = _wrap_gdal(mem_ds, warp_options)
    out_ds.FlushCache()
    gtiff.dataset = out_ds
    return gtiff