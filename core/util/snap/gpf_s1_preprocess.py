from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from esa_snappy import Product

from core.util import load_snap
from core.util.snap import build_apply_orbit_params, build_calib_params, build_terrain_correction_params, \
    build_thermal_noise_removal_params, build_topsar_deburst_params, build_speckle_filter_params

def apply_orbit_func(product:"Product", params:dict):
    GPF = load_snap('GPF')
    app_orb_params = build_apply_orbit_params(**params)
    ap_product = GPF.createProduct('Apply-Orbit-File', app_orb_params, product)
    return ap_product

def calibrate(product:"Product", params:dict) -> "Product":
    GPF = load_snap('GPF')
    calib_params = build_calib_params(**params)
    calib_product = GPF.createProduct('Calibration', calib_params, product)
    return calib_product

def thermal_noise_removal(product:"Product", params:dict):
    GPF = load_snap('GPF')
    tnr_params = build_thermal_noise_removal_params(**params)
    tnr_product = GPF.createProduct('ThermalNoiseRemoval', tnr_params, product)
    return tnr_product

def terrain_correction_func(product:"Product", params:dict):
    GPF = load_snap('GPF')
    tc_params = build_terrain_correction_params(**params)
    tc_product = GPF.createProduct('Terrain-Correction', tc_params, product)
    return tc_product

def topsar_deburst(product:"Product", params:dict):
    GPF = load_snap('GPF')
    td_params = build_topsar_deburst_params(**params)
    td_product = GPF.createProduct('TOPSAR-Deburst', td_params, product)
    return td_product

def speckle_filter(product:"Product", params:dict):
    GPF = load_snap('GPF')
    sf_params = build_speckle_filter_params(**params)
    sf_product = GPF.createProduct('Speckle-Filter', sf_params, product)
    return sf_product