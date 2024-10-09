import os, json


from core import ATMOS_SCRATCH_PATH
from core.util import load_ogr

def polygon_from_wkt(wkt, file=None):

    ogr = load_ogr()

    if file == None:
        file = ATMOS_SCRATCH_PATH + '/polygon.json'

    odir = os.path.dirname(file)
    if not os.path.exists(odir):
        os.makedirs(odir)

    geom = None
    if geom is None:
        try:
            geom = ogr.CreateGeometryFromWkt(wkt)
        except:
            pass

    if geom is None:
        try:
            geom = ogr.CreateGeometryFromJson(wkt)
        except:
            pass

    if geom is not None:
        with open(file, 'w') as f:
            f.write(geom.ExportToJson())
    geom = None

    if os.path.exists(file):
        return(file)
    else:
        return(None)
