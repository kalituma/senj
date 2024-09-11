from osgeo import osr

def make_transform(src_epsg, tar_epsg):
    source_spatial_ref = osr.SpatialReference()
    source_spatial_ref.ImportFromEPSG(src_epsg)
    target_spatial_ref = osr.SpatialReference()
    target_spatial_ref.ImportFromEPSG(tar_epsg)
    return osr.CoordinateTransformation(source_spatial_ref, target_spatial_ref)

def transform_coords(lon, lat, source_epsg, target_epsg):
    transformer = make_transform(source_epsg, target_epsg)
    x, y, z = transformer.TransformPoint(lon, lat)
    return x, y