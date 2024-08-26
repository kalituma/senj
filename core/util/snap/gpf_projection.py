from esa_snappy import Product
from pyproj import Proj
from osgeo import osr
from core.util.snap import find_gt_from_product, find_proj_from_product, find_epsg_from_product

def projection_tif_snap(product:Product):
    transform = tuple(find_gt_from_product(product))
    Wkt = find_proj_from_product(product)
    dimx, dimy = product.getSceneRasterWidth(), product.getSceneRasterHeight()
    epsg = find_epsg_from_product(product)

    src = osr.SpatialReference()
    src.ImportFromWkt(Wkt)
    p = Proj(Wkt)

    x0 = transform[0]
    dx = transform[1]
    y0 = transform[3]
    dy = transform[5]

    pixel_size = [dx, dy]
    xrange = [x0, x0 + dimx * dx]
    yrange = [y0, y0 + dimy * dy]

    dct = {'p': p, 'epsg': epsg,
           'Wkt': Wkt, 'proj4_string': src.ExportToProj4(),  # p.crs.to_proj4()
           'xrange': xrange, 'yrange': yrange,
           'xdim': dimx, 'ydim': dimy,
           'dimensions': (dimx, dimy),
           'pixel_size': pixel_size}
    dct['projection'] = f'EPSG:{dct["epsg"]}'

    return dct