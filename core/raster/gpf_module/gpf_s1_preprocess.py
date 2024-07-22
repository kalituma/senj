from enum import Enum
from esa_snappy import GPF, Product
from core.raster.gpf_module import build_apply_orbit_params, build_calib_params, build_terrain_correction_params, \
    build_thermal_noise_removal_params, build_topsar_deburst_params, build_speckle_filter_params

NEAREST_NEIGHBOUR_NAME = "NEAREST_NEIGHBOUR"
BILINEAR_INTERPOLATION_NAME = "BILINEAR_INTERPOLATION"
CUBIC_CONVOLUTION_NAME = "CUBIC_CONVOLUTION"
BISINC_5_POINT_INTERPOLATION_NAME = "BISINC_5_POINT_INTERPOLATION"
BISINC_11_POINT_INTERPOLATION_NAME = "BISINC_11_POINT_INTERPOLATION"
BISINC_21_POINT_INTERPOLATION_NAME = "BISINC_21_POINT_INTERPOLATION"
BICUBIC_INTERPOLATION_NAME = "BICUBIC_INTERPOLATION"

COPERNICUS_30 = "Copernicus 30m Global DEM"
STRM_3SEC = "SRTM 3Sec"
STRM_1SEC_HGT = "SRTM 1Sec HGT"
SRTM_1SEC_GRD = "SRTM 1Sec Grid"
ASTER_1SEC = "ASTER 1Sec GDEM"
ACE30 = "ACE30"
ACE2_5 = "ACE2_5Min"
GETASSE30 = "GETASSE30"

class ORBIT_TYPE(Enum):
    SENTINEL_PRECISE = 'Sentinel Precise (Auto Download)'
    SENTINEL_RESTITUTED = 'Sentinel Restituted (Auto Download)'
    DORIS_POR = 'DORIS Preliminary POR (ENVISAT)'
    DORIS_VOR = 'DORIS Precise VOR (ENVISAT) (Auto Download)'
    DELFT_PRECISE = 'DELFT Precise (ENVISAT, ERS1&2) (Auto Download)'
    PRARE_PRECISE = 'PRARE Precise (ERS1&2) (Auto Download)'
    K5_PRECISE = 'Kompsat5 Precise'

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for orbit_type in cls:
            if orbit_type.value == value:
                return orbit_type
        return None


def apply_orbit_func(product:Product, params:dict):
    app_orb_params = build_apply_orbit_params(**params)
    ap_product = GPF.createProduct('Apply-Orbit-File', app_orb_params, product)
    return ap_product

def calibrate(product:Product, params:dict):

    calib_params = build_calib_params(**params)
    calib_product = GPF.createProduct('Calibration', calib_params, product)
    return calib_product

def thermal_noise_removal(product:Product, params:dict):
    tnr_params = build_thermal_noise_removal_params(**params)
    tnr_product = GPF.createProduct('ThermalNoiseRemoval', tnr_params, product)
    return tnr_product

def terrain_correction_func(product:Product, params:dict):
    tc_params = build_terrain_correction_params(**params)
    tc_product = GPF.createProduct('Terrain-Correction', tc_params, product)
    return tc_product

def topsar_deburst(product:Product, params:dict):
    td_params = build_topsar_deburst_params(**params)
    td_product = GPF.createProduct('TOPSAR-Deburst', td_params, product)
    return td_product

def speckle_filter(product:Product, params:dict):
    sf_params = build_speckle_filter_params(**params)
    sf_product = GPF.createProduct('Speckle-Filter', sf_params, product)
    return sf_product