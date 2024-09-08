import numpy as np
import scipy.ndimage, scipy.interpolate

from core.atmos.ac.ancillary import get
from core.util import Logger

def load_ancillary_data(l1r:dict, l1r_band_list:list, global_attrs:dict, user_settings:dict) -> dict:

    def _load_params():
        ancillary_data = user_settings['ancillary_data']
        pressure = user_settings['pressure']
        wind = user_settings['wind']
        pressure_default = user_settings['pressure_default']
        auxiliary_default = user_settings['s2_auxiliary_default']
        auxiliary_interpolate = user_settings['s2_auxiliary_interpolate']
        return ancillary_data, pressure, pressure_default, wind, auxiliary_default, auxiliary_interpolate

    ancillary_data, pressure, pressure_default, wind, auxiliary_default, auxiliary_interpolate = _load_params()

    if ancillary_data and ('lat' in l1r and 'lon' in l1r) or ('lat' in global_attrs and 'lon' in global_attrs):

        if 'lat' in l1r and 'lon' in l1r:
            clon = np.nanmedian(l1r['lon'])
            clat = np.nanmedian(l1r['lat'])
        else:
            clon = global_attrs['lon']
            clat = global_attrs['lat']

        Logger.get_logger().log('info', f'Getting ancillary data for {global_attrs["isodate"]} {clon:.3f}E {clat:.3f}N')
        # load ancillary data at center location : ['uoz', 'uwv', 'z_wind', 'm_wind', 'pressure']
        anc = get(global_attrs['isodate'], clon, clat, verbosity=1)

        for k in ['uoz', 'uwv', 'wind', 'pressure']:
            if k == 'pressure':
                if pressure != pressure_default:
                    continue
            if k == 'wind' and wind is not None:
                continue

            if k in anc:
                global_attrs[k] = 1.0 * anc[k]

        del clon, clat, anc
    else:
        if auxiliary_default and global_attrs['sensor'][0:2] == 'S2' and global_attrs['sensor'][4:] == 'MSI':
            ## get mid point values from AUX ECMWFT
            if 'AUX_ECMWFT_msl_values' in global_attrs:
                global_attrs['pressure'] = global_attrs['AUX_ECMWFT_msl_values'][int(len(global_attrs['AUX_ECMWFT_msl_values'])/2)]/100 # convert from Pa to hPa
            if 'AUX_ECMWFT_tco3_values' in global_attrs:
                global_attrs['uoz'] = global_attrs['AUX_ECMWFT_tco3_values'][int(len(global_attrs['AUX_ECMWFT_tco3_values'])/2)] ** -1 * 0.0021415 # convert from kg/m2 to cm-atm
            if 'AUX_ECMWFT_tcwv_values' in global_attrs:
                global_attrs['uwv'] = global_attrs['AUX_ECMWFT_tcwv_values'][int(len(global_attrs['AUX_ECMWFT_tcwv_values'])/2)]/10 # convert from kg/m2 to g/cm2
            if 'AUX_ECMWFT__0u_values' in global_attrs and 'AUX_ECMWFT__0v_values' in global_attrs:  # S2Resampling, msiresampling
                u_wind = global_attrs['AUX_ECMWFT__0u_values'][int(len(global_attrs['AUX_ECMWFT__0u_values'])/2)]
                v_wind = global_attrs['AUX_ECMWFT__0v_values'][int(len(global_attrs['AUX_ECMWFT__0v_values'])/2)]
                global_attrs['wind'] = np.sqrt(u_wind * u_wind + v_wind * v_wind)

            ## interpolate to scene centre
            if auxiliary_interpolate:
                if 'lat' in l1r_band_list and 'lon' in l1r_band_list:
                    clon = np.nanmedian(l1r['lon'])
                    clat = np.nanmedian(l1r['lon'])
                else:
                    clon = global_attrs['lon']
                    clat = global_attrs['lat']
                ## pressure
                aux_par = 'ECMWFT_msl'
                if f'AUX_{aux_par}_values' in global_attrs:
                    lndi = scipy.interpolate.LinearNDInterpolator((global_attrs[f'AUX_{aux_par}_longitudes'],
                                                                   global_attrs[f'AUX_{aux_par}_latitudes']),
                                                                   global_attrs[f'AUX_{aux_par}_values'])
                    global_attrs['pressure'] = lndi(clon, clat)/100 # convert from Pa to hPa
                    del lndi
                elif 'msl' in l1r_band_list:  # S2Resampling, msiresampling
                    lndi = l1r['msl']
                    global_attrs['pressure'] = lndi(lndi.len/2, lndi.len/2) / 100  # convert from Pa to hPa
                    del lndi
                ## ozone
                aux_par = 'ECMWFT_tco3'
                if f'AUX_{aux_par}_values' in global_attrs:
                    lndi = scipy.interpolate.LinearNDInterpolator((global_attrs[f'AUX_{aux_par}_longitudes'],
                                                                   global_attrs[f'AUX_{aux_par}_latitudes']),
                                                                   global_attrs[f'AUX_{aux_par}_values'])
                    global_attrs['uoz'] = lndi(clon, clat)**-1 * 0.0021415 # convert from kg/m2 to cm-atm
                    del lndi
                ## water vapour
                aux_par = 'ECMWFT_tcwv'
                if f'AUX_{aux_par}_values' in global_attrs:
                    lndi = scipy.interpolate.LinearNDInterpolator((global_attrs[f'AUX_{aux_par}_longitudes'],
                                                                   global_attrs[f'AUX_{aux_par}_latitudes']),
                                                                   global_attrs[f'AUX_{aux_par}_values'])
                    global_attrs['uwv'] = lndi(clon, clat)/10 # convert from kg/m2 to g/cm2
                    del lndi
                elif 'tcwv' in l1r_band_list:
                    lndi = l1r['tcwv']
                    global_attrs['uwv'] = lndi(lndi.len/2, lndi.len/2) / 10  # convert from kg/m2 to g/cm2
                    del lndi
                del clon, clat


    return global_attrs