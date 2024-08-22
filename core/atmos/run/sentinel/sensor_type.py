def get_sensor_type(l1r_meta:dict) -> str:
    if l1r_meta['SPACECRAFT_NAME'] == 'Sentinel-2A':
        return 'S2A_MSI'
    elif l1r_meta['SPACECRAFT_NAME'] == 'Sentinel-2B':
        return 'S2B_MSI'
    else:
        raise NotImplementedError(f'{l1r_meta["SPACECRAFT_NAME"]} is not implemented.')