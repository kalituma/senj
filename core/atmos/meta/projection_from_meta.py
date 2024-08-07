from pyproj import Proj
from core.util import epsg_to_proj4

def projection_from_granule_meta(granule_meta:dict, s2_target_res:int=10, return_grids:bool=False):

    is_utm = True
    is_ps = False

    cs_code = granule_meta["HORIZONTAL_CS_CODE"]
    cs_name = granule_meta["HORIZONTAL_CS_NAME"]
    epsg = int(cs_code.split(':')[1])


    split = cs_name.split('/')
    datum = split[0].strip()
    zone_name = split[1].split()[-1]

    # if 32600 < epsg <= 32660:
    #     zone = epsg - 32600
    #     proj4_list = ['+proj=utm', f'+zone={zone}', f'+datum={datum}', '+units=m', '+no_defs ']
    #
    # if 32700 < epsg <= 32760:
    #     zone = epsg - 32700
    #     proj4_list = ['+proj=utm', f'+zone={zone}', '+south', f'+datum={datum}', '+units=m', '+no_defs ']

    # proj4_string = ' '.join(proj4_list)

    proj4_string = epsg_to_proj4(epsg)

    p = Proj(proj4_string)

    ## construct 10, 20 and 60m grids
    grids = _build_grid(granule_meta, 'GRIDS')
    ## select target grid here and return projection dict
    proj_dict = _make_proj_dct(grids, s2_target_res, p, proj4_string, is_utm, is_ps, zone_name)

    if return_grids:
        return proj_dict, grids
    else:
        return proj_dict


def _build_grid(meta, grid_key):
    grids = {}
    for res in meta[grid_key].keys():
        grid = meta[grid_key][res]
        x0 = float(grid['ULX'])
        y0 = float(grid['ULY'])
        xs = float(grid['XDIM'])
        ys = float(grid['YDIM'])
        nx = float(grid['NCOLS'])
        ny = float(grid['NROWS'])

        x1 = x0 + (xs * nx)
        y1 = y0 + (ys * ny)
        xrange = (x0, x1)
        yrange = (y0, y1)
        grids[res] = {'xrange': xrange, 'yrange': yrange, 'nx': nx, 'ny': ny,
                         'x0': x0, 'xs': xs, 'x1': x1, 'y0': y0, 'ys': ys, 'y1': y1}
    return grids

def _make_proj_dct(grids, s2_target_res:int, p, proj4_string, is_utm, is_ps, zone_name):

    sel_or_grid = grids[f'{s2_target_res}']

    dimensions = sel_or_grid['nx'], sel_or_grid['ny']
    pixel_size = sel_or_grid['xs'], sel_or_grid['ys']

    dct = {'p': p, 'epsg': p.crs.to_epsg(),
              'xrange': [sel_or_grid['xrange'][0], sel_or_grid['xrange'][1]],
              'yrange': [sel_or_grid['yrange'][0], sel_or_grid['yrange'][1]],
              'proj4_string': proj4_string, 'dimensions': dimensions,
              'pixel_size': pixel_size, 'utm': is_utm, 'ps': is_ps}

    if is_utm: dct['zone']: zone_name

    ## offset end of range by one pixel to make correct lat/lon x/y datasets
    dct['xdim'] = int((dct['xrange'][1] - dct['xrange'][0]) / dct['pixel_size'][0])
    dct['ydim'] = int((dct['yrange'][1] - dct['yrange'][0]) / dct['pixel_size'][1])

    return dct

