
def prepare_attr_band_ds(band_ds, rsrd, user_settings:dict, rhot_names:list, transmit_gas:dict):
    for bi, band_slot in enumerate(rsrd['rsr_bands']):
        band_key = f'B{band_slot}'
        if band_key in band_ds:
            for k in ['wave_mu', 'wave_nm', 'wave_name']:
                if band_slot in rsrd[k]:
                    band_ds[band_key]['att'][k] = rsrd[k][band_slot]

            band_ds[band_key]['att']['rhot_ds'] = f'rhot_{band_ds[band_key]["att"]["wave_name"]}'
            band_ds[band_key]['att']['rhos_ds'] = f'rhos_{band_ds[band_key]["att"]["wave_name"]}'

            if user_settings['add_band_name']:
                band_ds[band_key]["att"]['rhot_ds'] = f'rhot_{band_slot}_{band_ds[band_key]["att"]["wave_name"]}'
                band_ds[band_key]["att"]['rhos_ds'] = f'rhos_{band_slot}_{band_ds[band_key]["att"]["wave_name"]}'
            if user_settings['add_detector_name']:
                dsname = rhot_names[bi][5:]
                band_ds[band_key]["att"]['rhot_ds'] = f'rhot_{dsname}'
                band_ds[band_key]["att"]['rhos_ds'] = f'rhos_{dsname}'

            for k in transmit_gas:
                if k not in ['wave']:
                    band_ds[band_key]['att'][k] = transmit_gas[k][band_slot]
                    if user_settings['gas_transmittance'] is False:
                        band_ds[band_key]['att'][k] = 1.0
            band_ds[band_key]['att']['wavelength'] = band_ds[band_key]['att']['wave_nm']
    ## end bands dataset
    del rhot_names, transmit_gas

    return band_ds