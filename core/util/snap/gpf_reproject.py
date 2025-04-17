from typing import TYPE_CHECKING
from core.util import epsg_to_wkt, load_snap
from core.util.snap import build_reproject_params

if TYPE_CHECKING:
    from esa_snappy import Product

def reproject_gpf(product:"Product", params:dict):
    GPF = load_snap('GPF')
    # params['crs'] = epsg_to_wkt(int(params['crs'][5:]))
    if '4326' in params['crs']:
        params['crs'] = 'WGS84(DD)'
    rp_params = build_reproject_params(**params)
    sf_product = GPF.createProduct('Reproject', rp_params, product)
    return sf_product