import unittest

from Py6S import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Test6SRSR(unittest.TestCase):

    def load_lut(self):
        pass

    def setup_6s_for_sentinel(self, s, date, lat, lon, wind_speed, sza, rho, tau, gases):

        s.geometry.day = date.day
        s.geometry.month = date.month
        s.geometry.year = date.year
        s.geometry.latitude = lat
        s.geometry.longitude = lon

        s.atmos_profile = AtmosProfile.UserWaterAndOzone(gases['water'], gases['ozone'])
        s.aero_profile = AeroProfile.Maritime
        s.aot550 = tau

        s.ground_reflectance = GroundReflectance.HomogeneousLambertian(rho)

        s.geometry.solar_z = sza
        s.geometry.solar_a = 0
        s.geometry.view_z = 0
        s.geometry.view_a = 0


    # def test_build_rsr(self):

    def test_estimate_kompsat_parameters(self):

        sentinel_data = {
            'date': pd.Timestamp('2023-06-15'),
            'lat': 37.5,
            'lon': 127.0,
            'wind_speed': 5.0,
            'sza': 30.0,
            'rho': 0.3,
            'tau': 0.2,
            'gases': {'water': 2.0, 'ozone': 0.3}
        }


        kompsat_wavelengths = [450, 550, 650, 850]

        s = SixS()
        results = []

        for wavelength in kompsat_wavelengths:
            self.setup_6s_for_sentinel(s, sentinel_data['date'], sentinel_data['lat'], sentinel_data['lon'],
                                  sentinel_data['wind_speed'], sentinel_data['sza'],
                                  sentinel_data['rho'], sentinel_data['tau'], sentinel_data['gases'])

            s.wavelength = Wavelength(wavelength/1000)
            s.run()

            results.append({
                'wavelength': wavelength,
                'transmission': s.outputs.transmittance_total_scattering.total,
                'path_radiance': s.outputs.path_radiance,
                'spherical_albedo': s.outputs.spherical_albedo
            })

        # return pd.DataFrame(results)

