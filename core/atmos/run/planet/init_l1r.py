from core.util import projection_geo

def init_l1r(dct_prj, output_geolocation:bool, output_xy:bool):
    l1r = {}

    if output_geolocation:
        lon, lat = projection_geo(dct_prj, add_half_pixel=True)
        l1r['lon'] = lon
        lon = None
        l1r['lat'] = lat
        lat = None

    ## write x/y
    if output_xy:
        x, y = projection_geo(dct_prj, xy=True, add_half_pixel=True)
        l1r['xm'] = x
        x = None
        l1r['ym'] = y
        y = None

    return l1r