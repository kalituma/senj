from osgeo import osr, ogr

def is_epsg_code_valid(epsg:int):
    srs = osr.SpatialReference()
    err = srs.ImportFromEPSG(epsg)
    if err != ogr.OGRERR_NONE:
        raise ValueError(f'Invalid epsg code: {epsg}')
    return True

def unit_from_wkt(wkt:str):
    srs = osr.SpatialReference()
    err = srs.ImportFromWkt(wkt)
    if err != ogr.OGRERR_NONE:
        raise ValueError(f'Invalid wkt: {wkt}')
    return get_unit(srs)

def unit_from_epsg(epsg:int):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    return get_unit(srs)

def get_unit(srs):
    linear_units = srs.GetLinearUnits()
    angular_units = srs.GetAngularUnits()

    is_projected = srs.IsProjected()

    if is_projected:
        unit_name = srs.GetLinearUnitsName()
        unit_value = linear_units
    else:
        unit_name = srs.GetAngularUnitsName()
        unit_value = angular_units

    return {
        "is_projected": is_projected,
        "unit_name": unit_name,
        "unit_value": unit_value
    }
