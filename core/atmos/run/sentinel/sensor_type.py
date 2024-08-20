
def get_sensor_type(band_meta:dict) -> str:
    if band_meta['SPACECRAFT_NAME'] == 'Sentinel-2A':
        return 'S2A_MSI'
    elif band_meta['SPACECRAFT_NAME'] == 'Sentinel-2B':
        return 'S2B_MSI'
    else:
        raise NotImplementedError(f'{band_meta["SPACECRAFT_NAME"]} is not implemented.')