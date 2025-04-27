import warnings
from core.util import load_ogr, load_osr

def wkt_to_ds(wkt:str, epsg:int):
    osr, ogr = load_osr(), load_ogr()

    mem_ds_name = '/vsimem/cutline_memory'
    mem_driver = ogr.GetDriverByName('MEMORY')
    mem_ds = mem_driver.CreateDataSource(mem_ds_name)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)

    nlayer = 'cutline_layer'
    layer = mem_ds.CreateLayer(nlayer, srs, ogr.wkbPolygon)

    feature_def = layer.GetLayerDefn()
    feature = ogr.Feature(feature_def)
    polygon = ogr.CreateGeometryFromWkt(wkt)
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)
    mem_ds.FlushCache()

    return mem_ds_name, nlayer

def wkt_to_epsg(wkt:str) -> int:
    osr = load_osr()

    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(wkt)
    code = spatial_ref.GetAuthorityCode(None)
    if code == None:
        warning_msg = f"Cannot identify EPSG code from WKT: {wkt}"
        warnings.warn(warning_msg)
        return 0
    else:
        return int(code)

def epsg_to_wkt(epsg:int):
    osr = load_osr()

    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(epsg)
    return spatial_ref.ExportToWkt()

def epsg_to_proj4(epsg:int):
    osr = load_osr()

    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(epsg)
    return spatial_ref.ExportToProj4()