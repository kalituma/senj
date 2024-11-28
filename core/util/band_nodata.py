import numpy as np

def set_nodata_to_band_dict(bands:dict, no_data_value:float) -> dict:
    for key, value in bands.items():

        value['value'] = value['value'].astype(float)

        default_nodata = value['no_data']
        value['no_data'] = no_data_value
        if not np.isnan(default_nodata):
            value['value'][value['value'] == default_nodata] = no_data_value
        else:
            value['value'][np.isnan(value['value'])] = no_data_value
    return bands