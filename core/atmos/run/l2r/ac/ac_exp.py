import numpy as np

import core.atmos as atmos

def apply_ac_exp(band_ds:dict, l1r_band_list, data_mem, rsrd: dict, luts, lutdw, par,
                 user_settings: dict, global_attrs: dict):

    def _get_params():
        wave1 = user_settings['exp_wave1']
        wave2 = user_settings['exp_wave2']
        l2w_mask_wave = user_settings['l2w_mask_wave']
        swir_threshold = user_settings['exp_swir_threshold']
        fixed_epsilon = user_settings['exp_fixed_epsilon']
        gamma = user_settings['exp_gamma']
        alpha = user_settings['exp_alpha']
        alpha_weighted = user_settings['exp_alpha_weighted']
        fixed_aerosol_reflectance = user_settings['exp_fixed_aerosol_reflectance']
        fixed_epsilon_percentile = user_settings['exp_fixed_epsilon_percentile']
        exp_epsilon = user_settings['exp_epsilon']
        output_intermediate = user_settings['exp_output_intermediate']

        return wave1, wave2, l2w_mask_wave, swir_threshold, fixed_epsilon, gamma, alpha, alpha_weighted, \
            fixed_aerosol_reflectance, fixed_epsilon_percentile, exp_epsilon, output_intermediate

    wave1, wave2, l2w_mask_wave, swir_threshold, fixed_epsilon, gamma, alpha, alpha_weighted, \
        fixed_aerosol_reflectance, fixed_epsilon_percentile, exp_epsilon, output_intermediate = _get_params()

    ## find bands to use
    exp_b1 = None
    exp_b1_diff = 1000
    exp_b2 = None
    exp_b2_diff = 1000
    exp_mask = None
    exp_mask_diff = 1000

    for band_slot, b_v in band_ds.items():
        sd = np.abs(b_v['att']['wave_nm'] - wave1)
        if (sd < 100) & (sd < exp_b1_diff):
            exp_b1_diff = sd
            exp_b1 = band_slot
            short_wv = b_v['att']['wave_nm']
        sd = np.abs(b_v['att']['wave_nm'] - wave2)
        if (sd < 100) & (sd < exp_b2_diff):
            exp_b2_diff = sd
            exp_b2 = band_slot
            long_wv = b_v['att']['wave_nm']
        sd = np.abs(b_v['att']['wave_nm'] - l2w_mask_wave)
        if (sd < 100) & (sd < exp_mask_diff):
            exp_mask_diff = sd
            exp_mask = band_slot
            mask_wv = b_v['att']['wave_nm']

    if (exp_b1 is None) or (exp_b2 is None):
        raise ValueError('Stopped: EXP bands not found in L1R bands')

    # print(f'Selected bands {exp_b1} and {exp_b2} for EXP processing')
    if (band_ds[exp_b1]['att']['rhot_ds'] not in l1r_band_list) | ( band_ds[exp_b2]['att']['rhot_ds'] not in l1r_band_list):
        # print(f'Selected bands are not available in {user_settings["inputfile"]}')
        if (band_ds[exp_b1]['att']['rhot_ds'] not in l1r_band_list):
            print(f'EXP B1: {band_ds[exp_b1]["att"]["rhot_ds"]}')
        if (band_ds[exp_b2]['att']['rhot_ds'] not in l1r_band_list):
            print(f'EXP B2: {band_ds[exp_b2]["att"]["rhot_ds"]}')
        return ()

    ## determine processing option
    if short_wv < 900 and long_wv < 900:
        exp_option = 'red/NIR'
    elif short_wv < 900 and long_wv > 1500:
        exp_option = 'NIR/SWIR'
    else:
        exp_option = 'SWIR'

    ## read data
    exp_d1 = band_ds[exp_b1]['data'] * 1.0
    exp_d2 = band_ds[exp_b2]['data'] * 1.0

    ## use mean geometry
    xi = [data_mem['pressure' + '_mean'][0][0],
          data_mem['raa' + '_mean'][0][0],
          data_mem['vza' + '_mean'][0][0],
          data_mem['sza' + '_mean'][0][0],
          data_mem['wind' + '_mean'][0][0]]

    exp_lut = luts[0]
    exp_cwlim = 0.005
    exp_initial_epsilon = 1.0

    ## Rayleigh reflectance
    rorayl_b1 = lutdw[exp_lut]['rgi'][exp_b1]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
    rorayl_b2 = lutdw[exp_lut]['rgi'][exp_b2]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))

    ## subtract Rayleigh reflectance
    exp_d1 -= rorayl_b1
    exp_d2 -= rorayl_b2

    ## compute mask
    if exp_mask == exp_b1:
        mask = exp_d1 >= user_settings['exp_swir_threshold']
    elif exp_mask == exp_b2:
        mask = exp_d2 >= user_settings['exp_swir_threshold']
    else:
        exp_dm = band_ds[exp_mask]["data"] * 1.0
        rorayl_mask = lutdw[exp_lut]['rgi'][exp_mask](
            (xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
        exp_dm -= rorayl_mask
        mask = exp_dm >= user_settings['exp_swir_threshold']
        exp_dm = None

    ## compute aerosol epsilon band ratio
    epsilon = exp_d1 / exp_d2
    epsilon[np.where(mask)] = np.nan

    ## red/NIR option
    exp_fixed_epsilon = False
    if user_settings['exp_fixed_epsilon']:
        exp_fixed_epsilon = True

    if exp_option == 'red/NIR':
        print('Using similarity spectrum for red/NIR EXP')
        exp_fixed_epsilon = True

        ## Rayleigh transmittances in both bands
        dtotr_b1 = lutdw[exp_lut]['rgi'][exp_b1](
            (xi[0], lutdw[exp_lut]['ipd']['dtott'], xi[1], xi[2], xi[3], xi[4], 0.001))
        utotr_b1 = lutdw[exp_lut]['rgi'][exp_b1](
            (xi[0], lutdw[exp_lut]['ipd']['utott'], xi[1], xi[2], xi[3], xi[4], 0.001))
        dtotr_b2 = lutdw[exp_lut]['rgi'][exp_b2](
            (xi[0], lutdw[exp_lut]['ipd']['dtott'], xi[1], xi[2], xi[3], xi[4], 0.001))
        utotr_b2 = lutdw[exp_lut]['rgi'][exp_b2](
            (xi[0], lutdw[exp_lut]['ipd']['utott'], xi[1], xi[2], xi[3], xi[4], 0.001))

        tr_b1 = (dtotr_b1 * utotr_b1 * band_ds[exp_b1]['att']['tt_gas'])
        tr_b2 = (dtotr_b2 * utotr_b2 * band_ds[exp_b2]['att']['tt_gas'])

        ## get gamma
        exp_gamma = tr_b1 / tr_b2 if user_settings['exp_gamma'] is None else float(user_settings['exp_gamma'])
        print(f'Gamma: {exp_gamma:.2f}')

        ## get alpha
        if user_settings['exp_alpha'] is None:
            ## import simspec
            simspec = atmos.shared.similarity_read()
            ## convolute to sensor_o
            if user_settings['exp_alpha_weighted']:
                ssd = atmos.shared.rsr_convolute_dict(simspec['wave'], simspec['ave'], rsrd['rsr'])
                exp_alpha = ssd[exp_b1] / ssd[exp_b2]
            ## or use closest bands
            else:
                ssi0, ssw0 = atmos.shared.closest_idx(simspec['wave'], band_ds[exp_b1]['att']['wave_mu'])
                ssi1, ssw1 = atmos.shared.closest_idx(simspec['wave'], band_ds[exp_b2]['att']['wave_mu'])
                exp_alpha = simspec['ave'][ssi0] / simspec['ave'][ssi1]
        else:
            exp_alpha = float(user_settings['exp_alpha'])
        print(f'Alpha: {exp_alpha:.2f}')

        ## first estimate of rhow to find clear waters
        exp_c1 = (exp_alpha / tr_b2) / (exp_alpha * exp_gamma - exp_initial_epsilon)
        exp_c2 = exp_initial_epsilon * exp_c1
        rhow_short = (exp_c1 * exp_d1) - (exp_c2 * exp_d2)

        ## additional masking for epsilon
        epsilon[(rhow_short < 0.) & (rhow_short > exp_cwlim)] = np.nan
        rhow_short = None

    elif exp_option == 'NIR/SWIR':
        print('Using NIR/SWIR EXP')
        exp_fixed_epsilon = True
        ## additional masking for epsilon
        mask2 = (exp_d2 < ((exp_d1 + 0.005) * 1.5)) & \
                (exp_d2 > ((exp_d1 - 0.005) * 0.8)) & \
                ((exp_d2 + 0.005) / exp_d1 > 0.8)
        epsilon[mask2] = np.nan
        mask2 = None
    elif exp_option == 'SWIR':
        print('Using SWIR EXP')
        if user_settings['exp_fixed_aerosol_reflectance']: exp_fixed_epsilon = True

    ## compute fixed epsilon
    if exp_fixed_epsilon:
        if user_settings['exp_epsilon'] is not None:
            epsilon = float(user_settings['exp_epsilon'])
        else:
            epsilon = np.nanpercentile(epsilon, user_settings['exp_fixed_epsilon_percentile'])

    ## determination of rhoam in long wavelength
    if exp_option == 'red/NIR':
        rhoam = (exp_alpha * exp_gamma * exp_d2 - exp_d1) / (exp_alpha * exp_gamma - epsilon)
    else:
        rhoam = exp_d2 * 1.0

    ## clear memory
    exp_d1, exp_d2 = None, None

    ## fixed rhoam?
    exp_fixed_rhoam = user_settings['exp_fixed_aerosol_reflectance']
    if exp_fixed_rhoam:
        rhoam = np.nanpercentile(rhoam, user_settings['exp_fixed_aerosol_reflectance_percentile'])
        # print(f'{user_settings["exp_fixed_aerosol_reflectance_percentile"]:.0f}th percentile rhoam ({long_wv} nm): {rhoam:.5f}')

    # print('EXP band 1', user_settings['exp_wave1'], exp_b1, band_ds[exp_b1]['att']['rhot_ds'])
    # print('EXP band 2', user_settings['exp_wave2'], exp_b2, band_ds[exp_b2]['att']['rhot_ds'])

    # if exp_fixed_epsilon:
    #     print(f'Epsilon: {epsilon:.2f}')

    ## output data
    if user_settings['exp_output_intermediate']:
        if not exp_fixed_epsilon:
            global_attrs['epsilon'] = epsilon
        if not exp_fixed_rhoam:
            global_attrs['rhoam'] = rhoam
    ## end exponential

    return rhoam, global_attrs