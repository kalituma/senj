import numpy as np
import os, glob, dateutil.parser, datetime, time
from typing import Union, TYPE_CHECKING


import core.atmos as atmos
from core.util import distance_se, rsr_read, rsr_convolute_dict, projection_read
from core.atmos.run.worldview import init_l1r, get_l1r_band

if TYPE_CHECKING:
    from core.raster import Raster

def build_worldview_l1r(target_raster: "Raster", meta_dict:dict, user_settings:dict,
                        convert_atmospherically_corrected = True,
                        percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    # init usersettings
    user_settings = atmos.setting.parse(meta_dict['sensor'], settings=user_settings)

    ## test if we need to do an atmospheric correction
    atmospherically_corrected = False
    if 'RADIOMETRICLEVEL' in meta_dict and 'RADIOMETRICENHANCEMENT' in meta_dict:
        if meta_dict['RADIOMETRICENHANCEMENT'] in ['ACOMP']:
            # print('Image {} is already corrected by supplier.'.format(bundle))
            # print('RADIOMETRICLEVEL: {} RADIOMETRICENHANCEMENT: {}'.format(meta['RADIOMETRICLEVEL'],meta['RADIOMETRICENHANCEMENT']))
            atmospherically_corrected = True

    band_names = [meta_dict['BAND_INFO'][b]['name'] for b in list(meta_dict['BAND_INFO'].keys())]

    raa = abs(float(meta_dict['MEANSUNAZ']) - float(meta_dict['MEANSATAZ']))
    while raa >= 180.: raa = np.abs(raa - 360)
    sza = 90. - float(meta_dict['MEANSUNEL'])
    vza = 90. - float(meta_dict['MEANSATEL'])

    output_geolocation = user_settings['output_geolocation']

    dtime = dateutil.parser.parse(meta_dict['isotime'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    rsrf = atmos.config['data_dir'] + f'/RSR/{meta_dict["sensor"]}.txt'
    rsr, rsr_bands = rsr_read(rsrf)
    waves = np.arange(250, 2500) / 1000
    waves_mu = rsr_convolute_dict(waves, waves, rsr)
    waves_names = { f'{b}': f'{waves_mu[b] * 1000:.0f}' for b in waves_mu }

    gains = None
    if user_settings['gains']:
        if len(user_settings['gains_toa']) == len(rsr_bands) and len(user_settings['offsets_toa']) == len(rsr_bands):
            gains = {}
            for bi, band in enumerate(rsr_bands):
                gains[band] = {'gain': float(user_settings['gains_toa'][bi]),
                               'offset': float(user_settings['offsets_toa'][bi])}
        else:
            print(f"Use of gains requested, but provided number of gain ({user_settings['gains_toa']}) or \
                             offset ({user_settings['offsets_toa']}) values does not match number of bands in RSR ({len(rsr_bands)})")
            print(f'Provide gains in band order: {",".join(rsr_bands)}')

    f0 = atmos.shared.f0_get(f0_dataset=user_settings['solar_irradiance_reference'])
    f0_b = rsr_convolute_dict(np.asarray(f0['wave'])/1000, np.asarray(f0['data'])*10, rsr)

    global_attrs = {
        'sensor': meta_dict['sensor'], 'satellite': meta_dict['satellite'],
        'isodate': isodate,  # 'global_dims':global_dims,
        'sza': sza, 'vza': vza, 'raa': raa, 'se_distance': se_distance,
        'mus': np.cos(sza * (np.pi / 180.)), 'acolite_file_type': 'L1R'
    }

    if atmospherically_corrected:
        global_attrs['acolite_file_type'] = 'converted'

    # skip the part for output specification
    ## add band info to gatts
    for b in rsr_bands:
        global_attrs[f'{b}_wave'] = waves_mu[b] * 1000
        global_attrs[f'{b}_name'] = waves_names[b]
        global_attrs[f'{b}_f0'] = f0_b[b]

    ## global scene dimensions from metadata
    global_dims = [int(meta_dict['NUMROWS']), int(meta_dict['NUMCOLUMNS'])]

    ## get projection info from tiles
    dct = None
    nc_projection = None
    warp_to = None

    ## get list of tiles in this bundle
    # ntiles = len(meta_dict['TILE_INFO'])
    raster_fn = os.path.basename(target_raster.path)

    file_exists = False
    tile_info = None
    for ti, tile_mdata in enumerate(meta_dict['TILE_INFO']):
        if raster_fn == tile_mdata['FILENAME']:
            file_exists = True
            tile_info = tile_mdata

    if not file_exists:
        raise ValueError(f'Raster file {raster_fn} not found in metadata.')

    dct = projection_read(target_raster.path)

    if dct is None and user_settings['worldview_projection']:
        bt = list(meta_dict['BAND_INFO'].keys())[0]
        lons = [meta_dict['BAND_INFO'][bt][k] for k in meta_dict['BAND_INFO'][bt] if 'LON' in k]
        lats = [meta_dict['BAND_INFO'][bt][k] for k in meta_dict['BAND_INFO'][bt] if 'LAT' in k]
        lim = [min(lats), min(lons), max(lats), max(lons)]
        dct, nc_projection, warp_to = atmos.shared.projection_setup(lim, user_settings['worldview_reproject_resolution'],
                                                                    res_method=user_settings['worldview_reproject_method'])
        global_dims = dct['ydim'], dct['xdim']

    ## final scene dimensions
    if dct is not None:
        ## compute dimensions
        dct['xdim'] = int(np.round((dct['xrange'][1] - dct['xrange'][0]) / dct['pixel_size'][0]))
        dct['ydim'] = int(np.round((dct['yrange'][1] - dct['yrange'][0]) / dct['pixel_size'][1]))
        ## these should match the global dims from metadata
        # if (global_dims[0] != dct['ydim']) | (global_dims[1] != dct['xdim']):
        #     print('Global dims and projection size do not match')
        #     print(global_dims[1], dct['xdim'])
        #     print(global_dims[0], dct['ydim'])

        ## add projection to gatts
        for k in ['xrange', 'yrange', 'proj4_string', 'pixel_size', 'dimensions', 'zone']:
            if k in dct:
                global_attrs[k] = dct[k]

        if nc_projection is None:
            nc_projection = atmos.shared.projection_netcdf(dct, add_half_pixel=False)

        global_attrs['projection_key'] = [k for k in nc_projection if k not in ['x', 'y']][0]

    l1r = init_l1r(dct, global_dims=global_dims, meta_dict=meta_dict, output_geolocation=output_geolocation)
    l1r['bands'] = get_l1r_band()

    return l1r
