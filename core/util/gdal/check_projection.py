from osgeo import osr, ogr
def is_epsg_code_valid(epsg:int):
    srs = osr.SpatialReference()
    err = srs.ImportFromEPSG(epsg)
    if err != ogr.OGRERR_NONE:
        raise ValueError(f'Invalid epsg code: {epsg}')
    return True