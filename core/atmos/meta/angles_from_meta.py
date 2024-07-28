import numpy as np


def build_angles(selected_resolution, det_bands, granule_meta, geometry_type, warp_option, rsr_bands, cur_dct):
    out = {}

    or_x_height = granule_meta['GRIDS'][f'{selected_resolution}']['NCOLS']
    or_y_height = granule_meta['GRIDS'][f'{selected_resolution}']['NROWS']

    xnew = np.linspace(0, granule_meta['VIEW']['Average_View_Zenith'].shape[1] - 1, int(or_x_height))
    ynew = np.linspace(0, granule_meta['VIEW']['Average_View_Zenith'].shape[0] - 1, int(or_y_height))
    sza = tiles_interp(granule_meta['SUN']['Zenith'], xnew, ynew, smooth=False, method='linear')
    saa = tiles_interp(granule_meta['SUN']['Azimuth'], xnew, ynew, smooth=False, method='linear')

    if geometry_type == 'grids':
        vza = tiles_interp(granule_meta['VIEW']['Average_View_Zenith'], xnew, ynew, smooth=False, method='nearest')
        vaa = tiles_interp(granule_meta['VIEW']['Average_View_Azimuth'], xnew, ynew, smooth=False, method='nearest')

    ## use s2 5x5 km grids with detector footprint interpolation
    dfoo = None
    bands = None
    if geometry_type == 'grids_footprint':

        # for band in product.getBands():
        band_name = res_band_map[f'{selected_resolution}']
        dfoo = det_bands[f'{band_name}']
        dval = np.unique(dfoo)

        bands = [str(bi) for bi, b in enumerate(rsr_bands)]

        vza = np.zeros((int(or_y_height), int(or_x_height))) + np.nan
        vaa = np.zeros((int(or_y_height), int(or_x_height))) + np.nan

        for nf, bv in enumerate(dval):
            if bv == 0:
                continue

            ave_vza = None
            ave_vaa = None

            for b in bands:
                if b not in granule_meta['VIEW_DET']:
                    continue
                if f'{bv}' not in granule_meta['VIEW_DET'][b]:
                    continue

                bza = granule_meta['VIEW_DET'][b][f'{bv}']['Zenith']
                baa = granule_meta['VIEW_DET'][b][f'{bv}']['Azimuth']
                bza = grid_extend(bza, iterations=1, crop=False)
                baa = grid_extend(baa, iterations=1, crop=False)
                if ave_vaa is None:
                    ave_vza = bza
                    ave_vaa = baa
                else:
                    ave_vza = np.dstack((ave_vza, bza))
                    ave_vaa = np.dstack((ave_vaa, baa))
            # if verbosity > 1: print('Computing band average per detector geometry')

            if ave_vza is not None:
                ave_vza = np.nanmean(ave_vza, axis=2)
                ave_vaa = np.nanmean(ave_vaa, axis=2)
                ## end compute detector average geometry
                ## interpolate grids to current detector
                det_mask = dfoo == bv

                ## add +1 to xnew and ynew since we are not cropping the extended grid
                vza[det_mask] = tiles_interp(ave_vza, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

                vaa[det_mask] = tiles_interp(ave_vaa, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

    src_params = get_src_param(granule_meta, selected_resolution, prefix="OR_")

    # resample to new geometry
    sza = warp_to(src_params, sza, warp_to=warp_option)
    saa = warp_to(src_params, saa, warp_to=warp_option)
    vza = warp_to(src_params, vza, warp_to=warp_option)
    vaa = warp_to(src_params, vaa, warp_to=warp_option)
    mask = (vaa == 0) * (vza == 0) * (saa == 0) * (sza == 0)

    out['dfoo'] = dfoo
    vza[mask] = np.nan
    sza[mask] = np.nan
    vaa[mask] = np.nan
    saa[mask] = np.nan
    out['vaa'] = vaa
    out['saa'] = saa
    out['vza'] = vza
    out['sza'] = sza

    raa = np.abs(saa - vaa)
    tmp = np.where(raa > 180)
    raa[tmp] = np.abs(360 - raa[tmp])
    raa[mask] = np.nan
    out['raa'] = raa

    lon, lat = projection_geo(cur_dct, add_half_pixel=True)
    out['lon'] = lon.astype(np.float32)
    out['lat'] = lat.astype(np.float32)

    return out

def get_angles_from_meta(granule_meta:dict):
    sza = granule_meta['SUN']['Mean_Zenith']
    saa = granule_meta['SUN']['Mean_Azimuth']
    vza = np.nanmean(granule_meta['VIEW']['Average_View_Zenith'])
    vaa = np.nanmean(granule_meta['VIEW']['Average_View_Azimuth'])
    raa = np.abs(saa - vaa)
    while raa > 180:
        raa = np.abs(360 - raa)

    return sza, saa, vza, vaa, raa