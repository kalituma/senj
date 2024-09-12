import re
from enum import Enum

class FILTER_WINDOW(Enum):
    SIZE_3x3 = '3x3'
    SIZE_5x5 = '5x5'
    SIZE_7x7 = '7x7'
    SIZE_9x9 = '9x9'
    SIZE_11x11 = '11x11'
    SIZE_13x13 = '13x13'
    SIZE_15x15 = '15x15'
    SIZE_17x17 = '17x17'
    SIZE_21x21 = '21x21'

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for filter_window in cls:
            if filter_window.value == value:
                return filter_window
        return None

class SPECKLE_FILTER(Enum):
    BOXCAR = 'Boxcar'
    MEDIAN = 'Median'
    FROST = 'Frost'
    GAMMA_MAP = 'Gamma Map'
    LEE_SPECKLE = 'Lee'
    LEE_REFINED = 'Refined Lee'
    LEE_SIGMA = 'Lee Sigma'
    IDAN = 'IDAN'
    MEAN_SPECKLE = 'Mean'

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for speckle_filter in cls:
            if speckle_filter.value == value:
                return speckle_filter
        return None

# SPECKLE FILTER


SIZE_3x3 = '3x3'
SIZE_5x5 = '5x5'
SIZE_7x7 = '7x7'
SIZE_9x9 = '9x9'
SIZE_11x11 = '11x11'
SIZE_13x13 = '13x13'
SIZE_15x15 = '15x15'
SIZE_17x17 = '17x17'
SIZE_21x21 = '21x21'

SIGMA_50 = 0.5
SIGMA_60 = 0.6
SIGMA_70 = 0.7
SIGMA_80 = 0.8
SIGMA_90 = 0.9


BAND_MAP = {
    'bands': [
        '{}',
        'B_detector_footprint_{}',
        'B_ancillary_lost_{}',
        'B_ancillary_degraded_{}',
        'B_msi_lost_{}',
        'B_msi_degraded_{}',
        'B_defective_{}',
        'B_nodata_{}',
        'B_partially_corrected_crosstalk_{}',
        'B_saturated_l1a_{}',
        'view_zenith_{}',
        'view_azimuth_{}'
    ],
    # 'view' : [
    #     'view_zenith_mean',
    #     'view_azimuth_mean'
    # ],
    'mask' : [
        'ancillary_lost_{}',
        'ancillary_degraded_{}',
        'msi_lost_{}',
        'msi_degraded_{}',
        'defective_{}',
        'nodata_{}',
        'partially_corrected_crosstalk_{}',
        'saturated_l1a_{}'
    ]
}

def get_default_bands(band_names:list[str]):
    default_bands = [band.format(name) for band in BAND_MAP['bands'] for name in band_names]
    # default_bands += BAND_MAP['view']
    return default_bands

def get_default_masks(mask_names:list[str]):
    bnum_pattern = '\d+'
    detector_footprint_band = [f"B{int(re.search(bnum_pattern, mask_name).group(0)):02}" if len(mask_name) == 2 else mask_name for mask_name in mask_names]
    default_masks = [mask.format(name) for mask in BAND_MAP['mask'] for name in mask_names]
    for i in range(1,13):
        for band in detector_footprint_band:
            default_masks += [f"detector_footprint-{band}-{i:02}"]
    return default_masks