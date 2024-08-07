from core.util import tiles_interp, grid_extend, projection_geo
from core.raster.gpf_module import get_src_param, warp_to
import numpy as np

def get_grid_width_height(grid_dict:dict, selected_resolution:str) -> tuple[int, int]:
    return grid_dict['GRIDS'][f'{selected_resolution}']['NCOLS'], grid_dict['GRIDS'][f'{selected_resolution}']['NROWS']

def build_angles(det_res:int, det_band:np.ndarray, granule_meta:dict, geometry_type:str, warp_option:tuple, index_to_band:list, proj_dict:dict) -> dict:

    out = {}

    width, height = get_grid_width_height(granule_meta, str(det_res))

    xnew = np.linspace(0, granule_meta['VIEW']['Average_View_Zenith'].shape[1] - 1, int(width))
    ynew = np.linspace(0, granule_meta['VIEW']['Average_View_Zenith'].shape[0] - 1, int(height))

    sza = tiles_interp(granule_meta['SUN']['Zenith'], xnew, ynew, smooth=False, method='linear')
    saa = tiles_interp(granule_meta['SUN']['Azimuth'], xnew, ynew, smooth=False, method='linear')

    if geometry_type == 'grids':
        vza = tiles_interp(granule_meta['VIEW']['Average_View_Zenith'], xnew, ynew, smooth=False, method='nearest')
        vaa = tiles_interp(granule_meta['VIEW']['Average_View_Azimuth'], xnew, ynew, smooth=False, method='nearest')

    ## use s2 5x5 km grids with detector footprint interpolation

    if geometry_type == 'grids_footprint':

        # for band in product.getBands():
        det_val = np.unique(det_band)

        bands = [str(bi) for bi, b in enumerate(index_to_band)]

        vza = np.zeros((int(height), int(width))) + np.nan
        vaa = np.zeros((int(height), int(width))) + np.nan

        for det_id, dev_value in enumerate(det_val):
            if dev_value == 0:
                continue

            ave_vza = None
            ave_vaa = None

            for band_id in bands:
                if band_id not in granule_meta['VIEW_DET']:
                    continue
                if f'{dev_value}' not in granule_meta['VIEW_DET'][band_id]:
                    continue

                bza = granule_meta['VIEW_DET'][band_id][f'{dev_value}']['Zenith']
                baa = granule_meta['VIEW_DET'][band_id][f'{dev_value}']['Azimuth']
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
                det_mask = det_band == dev_value

                ## add +1 to xnew and ynew since we are not cropping the extended grid
                vza[det_mask] = tiles_interp(ave_vza, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

                vaa[det_mask] = tiles_interp(ave_vaa, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

    src_params = get_src_param(granule_meta, det_res)

    # resample to new geometry
    sza = warp_to(src_params, sza, warp_to=warp_option)
    saa = warp_to(src_params, saa, warp_to=warp_option)
    vza = warp_to(src_params, vza, warp_to=warp_option)
    vaa = warp_to(src_params, vaa, warp_to=warp_option)
    mask = (vaa == 0) * (vza == 0) * (saa == 0) * (sza == 0)

    # out['det_band'] = det_band
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

    lon, lat = projection_geo(proj_dict, add_half_pixel=True)
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