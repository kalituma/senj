import numpy as np
import skimage.measure

from core.util import Logger

def _calcuate_var_means(var_mem, use_revlut:bool, per_pixel_geometry:bool,
                        var_mean:dict, l1r:dict, var_list:list, l1r_band_list:list):

    ## if path reflectance is tiled or resolved, use reverse lut
    ## no need to use reverse lut if fixed geometry is used
    ## we want to use the reverse lut to derive aot if the geometry data is resolved
    for var_name in var_list:
        if var_name not in l1r_band_list:
            var_mem[var_name] = var_mean[var_name]
        else:
            var_mem[var_name] = l1r[var_name]

        if len(np.atleast_1d(var_mem[var_name])) > 1:
            use_revlut = True  ## if any dataset more than 1 dimension use revlut
            per_pixel_geometry = True
        else:  ## convert floats into arrays
            var_mem[var_name] = np.asarray(var_mem[var_name])
            var_mem[var_name].shape += (1, 1)

        var_mem[f'{var_name}_mean'] = np.asarray(np.nanmean(var_mem[var_name]))  ## also store tile mean
        var_mem[f'{var_name}_mean'].shape += (1, 1)  ## make 1,1 dimensions

    return var_mem, use_revlut, per_pixel_geometry

def _tiling(var_mem:dict, var_list:list[str], per_pixel_geometry:bool, tile_dimensions, global_attrs:dict):


    method_changed = False
    ## for tiled processing track tile positions and average geometry
    tiles = []

    ni = np.ceil(global_attrs['data_dimensions'][0] / tile_dimensions[0]).astype(int)
    nj = np.ceil(global_attrs['data_dimensions'][1] / tile_dimensions[1]).astype(int)
    if ni <= 1 or nj <= 1:
        Logger.get_logger().log('info', f'Scene too small for tiling ({ni}x{nj} tiles of {tile_dimensions[0]}x{tile_dimensions[1]} pixels), using fixed processing')
        method_changed = True
    else:
        ntiles = ni * nj
        Logger.get_logger().log('info', f'Processing with {ntiles} tiles ({ni}x{nj} tiles of {tile_dimensions[0]}x{tile_dimensions[1]} pixels)')

        ## compute tile dimensions
        for ti in range(ni):
            for tj in range(nj):
                subti = [tile_dimensions[0] * ti,
                         tile_dimensions[0] * (ti + 1)]
                subti[1] = np.min((subti[1], global_attrs['data_dimensions'][0]))
                subtj = [tile_dimensions[1] * tj,
                         tile_dimensions[1] * (tj + 1)]
                subtj[1] = np.min((subtj[1], global_attrs['data_dimensions'][1]))
                tiles.append((ti, tj, subti, subtj))

        ## create tile geometry datasets
        for ds in var_list:
            if len(np.atleast_1d(var_mem[ds])) > 1:  ## if not fixed geometry
                var_mem[f'{ds}_tiled'] = np.zeros((ni, nj), dtype=np.float32) + np.nan
                for t in range(ntiles):
                    ti, tj, subti, subtj = tiles[t]
                    var_mem[f'{ds}_tiled'][ti, tj] = \
                        np.nanmean(var_mem[ds][subti[0]:subti[1], subtj[0]:subtj[1]])
            else:  ## if fixed geometry
                if per_pixel_geometry:
                    var_mem[f'{ds}_tiled'] = np.zeros((ni, nj), dtype=np.float32) + var_mem[ds]
                else:
                    var_mem[f'{ds}_tiled'] = 1.0 * var_mem[ds]

        ## remove full geom datasets as tiled will be used
        for ds in var_list:
            if f'{ds}_tiled' in var_mem:
                del var_mem[ds]
    ## end tiling

    return var_mem, tiles, method_changed

def _segmenting(var_mem, var_list, rhot_bands:dict, min_segment_size:int):

    method_changed = False
    segment_data = dict()

    ## set up image segments

    first_key = list(rhot_bands.keys())[0]
    finite_mask = np.isfinite(rhot_bands[first_key])
    segment_mask = skimage.measure.label(finite_mask)
    segments = np.unique(segment_mask)

    ## find and label segments
    for segment in segments:
        # if segment == 0: continue
        seg_sub = np.where((segment_mask == segment) & (finite_mask))
        # if len(seg_sub[0]) == 0: continue
        if len(seg_sub[0]) < max(1, min_segment_size):
            Logger.get_logger().log('info', f'Skipping segment of {len(seg_sub[0])} pixels')
            continue
        segment_data[segment] = {'segment': segment, 'sub': seg_sub}

    if len(segment_data) <= 1:
        Logger.get_logger().log('info', f'Image segmentation only found {len(segment_data)} segments')
        Logger.get_logger().log('info', 'Proceeding with dsf_aot_estimate=fixed')
        method_changed = True
    else:
        ## convert geometry and ancillary data
        for ds in var_list:
            if len(np.atleast_1d(var_mem[ds])) > 1:  ## if not fixed geometry
                var_mem['{}_segmented'.format(ds)] = [np.nanmean(var_mem[ds][segment_data[segment]['sub']])
                                                      for segment in segment_data]
            else:
                var_mem['{}_segmented'.format(ds)] = [1.0 * var_mem[ds] for segment in segment_data]
            var_mem['{}_segmented'.format(ds)] = np.asarray(var_mem['{}_segmented'.format(ds)]).flatten()
    ## end segmenting
    return var_mem, segment_data, method_changed

def build_l1r_mem(l1r:dict, var_mean:dict, var_list:list[str], l1r_band_list:list[str], rhot_bands:dict, user_settings:dict, global_attrs:dict, is_hyper:bool):

    def _load_params():

        if 'dsf_tile_dimensions' not in user_settings:
            user_settings['dsf_tile_dimensions'] = None

        aot_estimate:str = user_settings['dsf_aot_estimate']
        tile_dimensions: list[int] = user_settings['dsf_tile_dimensions']
        resolved_geometry:bool = user_settings['resolved_geometry']
        min_segment_size:int = user_settings['dsf_minimum_segment_size']

        return aot_estimate, tile_dimensions, resolved_geometry, min_segment_size

    aot_estimate, tile_dimensions, resolved_geometry, min_segment_size = _load_params()

    use_revlut = False
    per_pixel_geometry = False

    var_mem = {}
    var_mem, use_revlut, per_pixel_geometry = _calcuate_var_means(var_mem, use_revlut, per_pixel_geometry, var_mean=var_mean, l1r=l1r, var_list=var_list, l1r_band_list=l1r_band_list)

    tiles = None
    if aot_estimate == 'tiled' and tile_dimensions is not None:
        var_mem, tiles, method_changed = _tiling(var_mem, var_list, per_pixel_geometry, tile_dimensions=tile_dimensions, global_attrs=global_attrs)
        if method_changed:
            user_settings['dsf_aot_estimate'] = 'fixed'

    segment_data = None
    if aot_estimate == 'segmented':
        var_mem, segment_data, method_changed = _segmenting(var_mem, var_list, rhot_bands=rhot_bands, min_segment_size=min_segment_size)
        if method_changed:
            user_settings['dsf_aot_estimate'] = 'fixed'

    if not resolved_geometry and aot_estimate != 'tiled':
        use_revlut = False

    if aot_estimate in ['fixed', 'segmented']:
        use_revlut = False

    if is_hyper:
        use_revlut = False

    ## set LUT dimension parameters to correct shape if resolved processing
    if use_revlut and per_pixel_geometry and aot_estimate == 'resolved':
        for ds in var_list:
            if len(np.atleast_1d(var_mem[ds])) != 1:
                continue
            Logger.get_logger().log('info', f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]} pixels for resolved processing')
            var_mem[ds] = np.repeat(var_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    return var_mem, tiles, segment_data, use_revlut, per_pixel_geometry