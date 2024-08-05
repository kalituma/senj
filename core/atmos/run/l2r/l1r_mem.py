import numpy as np
import skimage.measure

def _calcuate_mean(data_mem, use_revlut:bool, per_pixel_geometry:bool,
                   l1r:dict, geom_mean:dict, mean_ds:list, l1r_ds:list):


    ## if path reflectance is tiled or resolved, use reverse lut
    ## no need to use reverse lut if fixed geometry is used
    ## we want to use the reverse lut to derive aot if the geometry data is resolved
    for ds in mean_ds:
        if ds not in l1r_ds:
            data_mem[ds] = geom_mean[ds]
        else:
            data_mem[ds] = l1r[ds]

        if len(np.atleast_1d(data_mem[ds])) > 1:
            use_revlut = True  ## if any dataset more than 1 dimension use revlut
            per_pixel_geometry = True
        else:  ## convert floats into arrays
            data_mem[ds] = np.asarray(data_mem[ds])
            data_mem[ds].shape += (1, 1)

        data_mem[f'{ds}_mean'] = np.asarray(np.nanmean(data_mem[ds]))  ## also store tile mean
        data_mem[f'{ds}_mean'].shape += (1, 1)  ## make 1,1 dimensions

    del geom_mean

    return data_mem, use_revlut, per_pixel_geometry

def _tiling(data_mem, mean_ds, user_settings, global_attrs, per_pixel_geometry):

    ## for tiled processing track tile positions and average geometry
    tiles = []
    if 'dsf_tile_dimensions' not in user_settings:
        user_settings['dsf_tile_dimensions'] = None

    if user_settings['dsf_aot_estimate'] == 'tiled' and user_settings['dsf_tile_dimensions'] is not None:
        ni = np.ceil(global_attrs['data_dimensions'][0] / user_settings['dsf_tile_dimensions'][0]).astype(int)
        nj = np.ceil(global_attrs['data_dimensions'][1] / user_settings['dsf_tile_dimensions'][1]).astype(int)
        if (ni <= 1) | (nj <= 1):
            # print(f'Scene too small for tiling ({ni}x{nj} tiles of {user_settings["dsf_tile_dimensions"][0]}x{user_settings["dsf_tile_dimensions"][1]} pixels), using fixed processing')
            user_settings['dsf_aot_estimate'] = 'fixed'
        else:
            ntiles = ni * nj
            # print('Processing with {} tiles ({}x{} tiles of {}x{} pixels)'.format(ntiles, ni, nj,user_settings['dsf_tile_dimensions'][0],user_settings['dsf_tile_dimensions'][1]))

            ## compute tile dimensions
            for ti in range(ni):
                for tj in range(nj):
                    subti = [user_settings['dsf_tile_dimensions'][0] * ti,
                             user_settings['dsf_tile_dimensions'][0] * (ti + 1)]
                    subti[1] = np.min((subti[1], global_attrs['data_dimensions'][0]))
                    subtj = [user_settings['dsf_tile_dimensions'][1] * tj,
                             user_settings['dsf_tile_dimensions'][1] * (tj + 1)]
                    subtj[1] = np.min((subtj[1], global_attrs['data_dimensions'][1]))
                    tiles.append((ti, tj, subti, subtj))

            ## create tile geometry datasets
            for ds in mean_ds:
                if len(np.atleast_1d(data_mem[ds])) > 1:  ## if not fixed geometry
                    data_mem[f'{ds}_tiled'] = np.zeros((ni, nj), dtype=np.float32) + np.nan
                    for t in range(ntiles):
                        ti, tj, subti, subtj = tiles[t]
                        data_mem[f'{ds}_tiled'][ti, tj] = \
                            np.nanmean(data_mem[ds][subti[0]:subti[1], subtj[0]:subtj[1]])
                else:  ## if fixed geometry
                    if per_pixel_geometry:
                        data_mem[f'{ds}_tiled'] = np.zeros((ni, nj), dtype=np.float32) + data_mem[ds]
                    else:
                        data_mem[f'{ds}_tiled'] = 1.0 * data_mem[ds]

            ## remove full geom datasets as tiled will be used
            for ds in mean_ds:
                if f'{ds}_tiled' in data_mem:
                    del data_mem[ds]
    ## end tiling

    return data_mem, tiles

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
        # if user_settings['verbosity'] > 3:
            # print(f'Found {len(segment_data)} segments')
        # for segment in segment_data:
            # if user_settings['verbosity'] > 4:
                # print(f'Segment {segment}/{len(segment_data)}: {len(segment_data[segment]["sub"][0])} pixels')
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

def build_l1r_mem(l1r, geom_mean, mean_ds, l1r_ds, rhot_bands, user_settings, global_attrs, is_hyper):

    use_revlut = False
    per_pixel_geometry = False

    data_mem = {}
    data_mem, use_revlut, per_pixel_geometry = _calcuate_mean(data_mem, use_revlut, per_pixel_geometry, l1r, geom_mean, mean_ds, l1r_ds)
    data_mem, tiles = _tiling(data_mem, mean_ds, user_settings, global_attrs, per_pixel_geometry)

    segment_data = {}
    if user_settings['dsf_aot_estimate'] == 'segmented':
        data_mem, segment_data = _segmenting(data_mem, mean_ds, rhot_bands, segment_data, user_settings)

    if (not user_settings['resolved_geometry']) & (user_settings['dsf_aot_estimate'] != 'tiled'):
        use_revlut = False
    if user_settings['dsf_aot_estimate'] in ['fixed', 'segmented']:
        use_revlut = False
    if is_hyper:
        use_revlut = False

    ## set LUT dimension parameters to correct shape if resolved processing
    if use_revlut and per_pixel_geometry and user_settings['dsf_aot_estimate'] == 'resolved':
        for ds in mean_ds:
            if len(np.atleast_1d(data_mem[ds])) != 1:
                continue
            # print(f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]} pixels for resolved processing')
            data_mem[ds] = np.repeat(data_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    return data_mem, tiles, segment_data, use_revlut, per_pixel_geometry