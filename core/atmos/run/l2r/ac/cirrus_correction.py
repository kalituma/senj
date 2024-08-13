import numpy as np

from core.util import rsr_convolute_nd

def correct_cirrus(band_table, l1r_band_list, var_mem, lut_mod_names, lut_table, ro_type, is_hyper, rsrd,
                   l2r, l2r_band_list, user_settings:dict):

    def _load_params():
        cirrus_range = user_settings['cirrus_range']
        return cirrus_range

    cirrus_range = _load_params()

    rho_cirrus = None

    ## use mean geometry to compute cirrus band Rayleigh
    xi = [var_mem['pressure' + '_mean'][0][0],
          var_mem['raa' + '_mean'][0][0],
          var_mem['vza' + '_mean'][0][0],
          var_mem['sza' + '_mean'][0][0],
          var_mem['wind' + '_mean'][0][0]]

    ## compute Rayleigh reflectance for hyperspectral sensors
    if is_hyper:
        rorayl_hyp = lut_table[lut_mod_names[0]]['rgi']((xi[0], lut_table[lut_mod_names[0]]['ipd'][ro_type],
                                                         lut_table[lut_mod_names[0]]['meta']['wave'], xi[1], xi[2], xi[3], xi[4],
                                                         0.001)).flatten()

    ## find cirrus bands
    for bi, band_slot, b_v in enumerate(band_table.items()):
        band_num = band_slot[1:]
        if ('rhot_ds' not in b_v['att']):
            continue
        if b_v['att']['rhot_ds'] not in l1r_band_list:
            continue
        if (b_v['att']['wave_nm'] < cirrus_range[0]):
            continue
        if (b_v['att']['wave_nm'] > cirrus_range[1]):
            continue

        ## compute Rayleigh reflectance
        if is_hyper:
            rorayl_cur = rsr_convolute_nd(rorayl_hyp, lut_table[lut_mod_names[0]]['meta']['wave'], rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)
        else:
            rorayl_cur = lut_table[lut_mod_names[0]]['rgi'][band_slot]((xi[0], lut_table[lut_mod_names[0]]['ipd'][ro_type], xi[1], xi[2], xi[3], xi[4], 0.001))

        ## cirrus reflectance = rho_t - rho_Rayleigh
        cur_data = band_table[band_slot]['data'] - rorayl_cur

        if rho_cirrus is None:
            rho_cirrus = cur_data * 1.0
        else:
            rho_cirrus = np.dstack((rho_cirrus, cur_data))
        cur_data = None

    if rho_cirrus is None:
        user_settings['cirrus_correction'] = False
    else:
        ## compute mean from several bands
        if len(rho_cirrus.shape) == 3:
            rho_cirrus = np.nanmean(rho_cirrus, axis=2)
        ## write cirrus mean
        l2r['rho_cirrus'] = rho_cirrus
        l2r_band_list.append('rho_cirrus')

    return rho_cirrus, l2r, l2r_band_list, user_settings