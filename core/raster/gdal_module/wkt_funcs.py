from osgeo import osr, ogr

def wkt_to_ds(wkt:str, epsg:int):
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
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(wkt)
    return int(spatial_ref.GetAuthorityCode(None))

def epsg_to_wkt(epsg:int):
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(epsg)
    return spatial_ref.ExportToWkt()