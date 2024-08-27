## def projection_read
## gets projection dict from target image file
## written by Quinten Vanhellemont, RBINS
## 2021-02-24
## modifications: 2022-08-06 (QV) added Wkt, set up Proj from Wkt
##                2022-12-13 (QV) use transform from world file if available
##                2024-03-28 (QV) x/y range and pixel_size as lists

from pyproj import Proj
from osgeo import gdal, osr
import os

def _find_world_transform(file):
    ## find world file if present
    for ext in ['J2W', 'TFW', 'WLD', 'j2w', 'tfw', 'wld']:
        fbase, fext = os.path.splitext(file)
        wfile = f'{fbase}.{ext}'
        if os.path.exists(wfile):
            break
        wfile = None

    ## read world file
    if wfile is not None:
        wtransform = []
        with open(wfile, 'r') as f:
            for l in f.readlines():
                wtransform.append(float(l.strip()))
        if len(wtransform) != 6:
            print('World file {} has wrong number of elements'.format(wfile))
            wtransform = None
    else:
        wtransform = None

    return wtransform

def projection_tif_gdal(ds, wtransform = None):

    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    dimx, dimy = ds.RasterXSize, ds.RasterYSize
    ds = None

    ## get projection info
    src = osr.SpatialReference()
    src.ImportFromWkt(projection)
    Wkt = src.ExportToWkt()
    p = Proj(Wkt)

    if wtransform is not None:
        ## world transform elements:
        ## 0 pixel X size
        ## 1 rotation about the Y axis (usually 0.0)
        ## 2 rotation about the X axis (usually 0.0)
        ## 3 negative pixel Y size
        ## 4 X coordinate of upper left pixel center
        ## 5 Y coordinate of upper left pixel center
        x0 = wtransform[4]
        dx = wtransform[0]
        y0 = wtransform[5]
        dy = wtransform[3]
    else:
        ## derive projection extent
        x0 = transform[0]
        dx = transform[1]
        y0 = transform[3]
        dy = transform[5]

    pixel_size = [dx, dy]
    xrange = [x0, x0 + dimx * dx]
    yrange = [y0, y0 + dimy * dy]

    ## make acolite generic dict
    dct = {'p': p, 'epsg': p.crs.to_epsg(),
           'Wkt': Wkt,  'proj4_string': src.ExportToProj4(), #p.crs.to_proj4()
           'xrange': xrange, 'yrange': yrange,
           'xdim':dimx, 'ydim': dimy,
           'dimensions':(dimx, dimy),
           'pixel_size': pixel_size}
    dct['projection'] = f'EPSG:{dct["epsg"]}'

    return dct

def projection_read(file:str):
    ## open file
    ds = gdal.Open(file)
    wtransform = _find_world_transform(file)
    return projection_tif_gdal(ds, wtransform)