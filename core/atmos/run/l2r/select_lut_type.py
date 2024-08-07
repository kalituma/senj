
def select_lut_type(global_attrs:dict, user_settings:dict):

    def _load_params():
        interface_reflectance = user_settings['dsf_interface_reflectance']
        interface_option = user_settings['dsf_interface_option']
        wind_default = user_settings['wind_default']

        return interface_reflectance, interface_option, wind_default

    interface_reflectance, interface_option, wind_default = _load_params()

    par = ''

    if interface_reflectance:
        if interface_option == 'default':
            par = 'romix+rsky_t'
        elif interface_option == '6sv':
            par = 'romix+rsurf'
            # print(par)
    else:
        par = 'romix'

    ## set wind to wind range
    if global_attrs['wind'] is None:
        global_attrs['wind'] = wind_default

    if par == 'romix+rsurf':
        global_attrs['wind'] = max(2, global_attrs['wind'])
        global_attrs['wind'] = min(20, global_attrs['wind'])
    else:
        global_attrs['wind'] = max(0.1, global_attrs['wind'])
        global_attrs['wind'] = min(20, global_attrs['wind'])

    return par, global_attrs