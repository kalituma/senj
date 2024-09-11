import numpy as np
import scipy.ndimage, scipy.interpolate

import core.atmos as atmos
from core.util import Logger

def band_data_fixed(band_data:np.ndarray, band_sub:np.ndarray, percentile, intercept_pixels, dsf_spectrum_option):

    band_data_copy = band_data * 1.0
    if dsf_spectrum_option == 'darkest':
        band_data = np.array((np.nanpercentile(band_data[band_sub], 0)))
    if dsf_spectrum_option == 'percentile':
        band_data = np.array((np.nanpercentile(band_data[band_sub], percentile)))
    if dsf_spectrum_option == 'intercept':
        band_data = atmos.shared.intercept(band_data[band_sub], intercept_pixels)
    band_data.shape += (1, 1)  ## make 1,1 dimensions
    gk = '_mean'
    dark_pixel_location = np.where(band_data_copy <= band_data)
    if len(dark_pixel_location[0]) != 0:
        dark_pixel_location_x = dark_pixel_location[0][0]
        dark_pixel_location_y = dark_pixel_location[1][0]
    Logger.get_logger().log('info', f'Dark pixel location: {dark_pixel_location_x}, {dark_pixel_location_y}')
    # print(band_data)
    # if not use_revlut:
    #    gk='_mean'
    # else:
    #    band_data = np.tile(band_data, band_shape)
    # print(band_slot, user_settings['dsf_spectrum_option'], f'{float(band_data[0, 0]):.3f}')
    return band_data, gk

def band_data_tiled(band_data:np.ndarray, tiles:list,
                    percentile:float, intercept_pixels:int, dsf_spectrum_option:str, min_tile_cover:float):


    gk = '_tiled'
    ## tile this band data
    tile_data = np.zeros((tiles[-1][0] + 1, tiles[-1][1] + 1), dtype=np.float32) + np.nan
    for t_id in range(len(tiles)):
        ti, tj, t_y_range, t_x_range = tiles[t_id]
        tiled_band = band_data[t_y_range[0]:t_y_range[1], t_x_range[0]:t_x_range[1]]
        t_ele = (t_x_range[1] - t_x_range[0]) * (t_y_range[1] - t_y_range[0])
        n_finite = len(np.where(np.isfinite(tiled_band))[0])
        if n_finite < t_ele * float(min_tile_cover):
            continue

        ## get per tile darkest
        if dsf_spectrum_option == 'darkest':
            tile_data[ti, tj] = np.array((np.nanpercentile(tiled_band, 0)))
        if dsf_spectrum_option == 'percentile':
            tile_data[ti, tj] = np.array((np.nanpercentile(tiled_band, percentile)))
        if dsf_spectrum_option == 'intercept':
            tile_data[ti, tj] = atmos.shared.intercept(tiled_band, int(intercept_pixels))
        del tiled_band

    ## fill nan tiles with closest values
    ind = scipy.ndimage.distance_transform_edt(np.isnan(tile_data), return_distances=False, return_indices=True)
    band_data = tile_data[tuple(ind)]
    del tile_data, ind

    return band_data, gk

def band_data_segmented(band_data:np.ndarray, segment_data:dict,
                        percentile, intercept_pixels, dsf_spectrum_option):

    gk = '_segmented'

    if dsf_spectrum_option == 'darkest':
        band_data = np.array([np.nanpercentile(band_data[segment_data[segment]['sub']], 0)[0] \
                              for segment in segment_data])
    if dsf_spectrum_option == 'percentile':
        band_data = np.array([np.nanpercentile(band_data[segment_data[segment]['sub']], percentile)[0] \
                              for segment in segment_data])
    if dsf_spectrum_option == 'intercept':
        band_data = np.array([atmos.shared.intercept(band_data[segment_data[segment]['sub']], intercept_pixels) \
                              for segment in segment_data])
    band_data.shape += (1, 1)  ## make 2 dimensions
    # if verbosity > 2: print(b, setu['dsf_spectrum_option'], ['{:.3f}'.format(float(v)) for v in band_data])

    return band_data, gk



def percentile_filter(band_data:np.ndarray, mask:np.ndarray, filter_box, percentile):
    # print(f'Filtered {b_v["att"]["rhot_ds"]} using {user_settings["dsf_filter_percentile"]}th percentile in {user_settings["dsf_filter_box"][0]}x{user_settings["dsf_filter_box"][1]} pixel box')
    band_data[mask] = np.nanmedian(band_data)  ## fill mask with median
    # band_data = scipy.ndimage.median_filter(band_data, size=setu['dsf_filter_box'])
    band_data = scipy.ndimage.percentile_filter(band_data, percentile, size=filter_box)
    band_data[mask] = np.nan

    return band_data