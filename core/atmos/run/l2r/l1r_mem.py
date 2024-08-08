import numpy as np
import skimage.measure

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

def _tiling(var_mem:dict, var_list:list[str], per_pixel_geometry:bool, user_settings:dict, global_attrs:dict):

    def _load_params():

        if 'dsf_tile_dimensions' not in user_settings:
            user_settings['dsf_tile_dimensions'] = None

        tile_dimensions:list[int] = user_settings['dsf_tile_dimensions']
        aot_estimate:str = user_settings['dsf_aot_estimate']
        return tile_dimensions, aot_estimate

    tile_dimensions, aot_estimate = _load_params()

    ## for tiled processing track tile positions and average geometry
    tiles = []

    if aot_estimate == 'tiled' and tile_dimensions is not None:
        ni = np.ceil(global_attrs['data_dimensions'][0] / tile_dimensions[0]).astype(int)
        nj = np.ceil(global_attrs['data_dimensions'][1] / tile_dimensions[1]).astype(int)
        if ni <= 1 or nj <= 1:
            # print(f'Scene too small for tiling ({ni}x{nj} tiles of {user_settings["dsf_tile_dimensions"][0]}x{user_settings["dsf_tile_dimensions"][1]} pixels), using fixed processing')
            user_settings['dsf_aot_estimate'] = 'fixed'
        else:
            ntiles = ni * nj
            # print('Processing with {} tiles ({}x{} tiles of {}x{} pixels)'.format(ntiles, ni, nj,user_settings['dsf_tile_dimensions'][0],user_settings['dsf_tile_dimensions'][1]))

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

    return var_mem, tiles

def _segmenting(data_mem, mean_ds, rhot_bands, segment_data, user_settings):

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
        if len(seg_sub[0]) < max(1, user_settings['dsf_minimum_segment_size']):
            # print('Skipping segment of {} pixels'.format(len(seg_sub[0])))
            continue
        segment_data[segment] = {'segment': segment, 'sub': seg_sub}

    if len(segment_data) <= 1:
        # print('Image segmentation only found {} segments'.format(len(segment_data)))
        # print('Proceeding with dsf_aot_estimate=fixed')
        user_settings['dsf_aot_estimate'] = 'fixed'
    else:
        ## convert geometry and ancillary data
        for ds in mean_ds:
            if len(np.atleast_1d(data_mem[ds])) > 1:  ## if not fixed geometry
                data_mem['{}_segmented'.format(ds)] = [np.nanmean(data_mem[ds][segment_data[segment]['sub']])
                                                       for segment in segment_data]
            else:
                data_mem['{}_segmented'.format(ds)] = [1.0 * data_mem[ds] for segment in segment_data]
            data_mem['{}_segmented'.format(ds)] = np.asarray(data_mem['{}_segmented'.format(ds)]).flatten()
    ## end segmenting
    return data_mem, segment_data

def build_l1r_mem(l1r:dict, var_mean:dict, var_list:list[str], l1r_band_list:list[str], rhot_bands:dict, user_settings:dict, global_attrs:dict, is_hyper:bool):

    def _load_params():
        aot_estimate:str = user_settings['dsf_aot_estimate']
        resolved_geometry:bool = user_settings['resolved_geometry']
        return aot_estimate, resolved_geometry

    aot_estimate, resolved_geometry = _load_params()

    use_revlut = False
    per_pixel_geometry = False

    var_mem = {}
    var_mem, use_revlut, per_pixel_geometry = _calcuate_var_means(var_mem, use_revlut, per_pixel_geometry, var_mean=var_mean, l1r=l1r, var_list=var_list, l1r_band_list=l1r_band_list)
    var_mem, tiles = _tiling(var_mem, var_list, per_pixel_geometry, user_settings=user_settings, global_attrs=global_attrs)

    segment_data = None
    if aot_estimate == 'segmented':
        segment_data = dict()
        var_mem, segment_data = _segmenting(var_mem, var_list, rhot_bands, segment_data, user_settings)

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
            # print(f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]} pixels for resolved processing')
            var_mem[ds] = np.repeat(var_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    return var_mem, tiles, segment_data, use_revlut, per_pixel_geometry