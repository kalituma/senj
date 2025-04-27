from typing import TYPE_CHECKING
from core.util import load_snap
from core.util.snap import get_default_bands, get_default_masks
from core.util.snap.gpf_const import SPECKLE_FILTER

if TYPE_CHECKING:
    from esa_snappy import HashMap

def _build_params(params: "HashMap"=None, **kwargs):

    HashMap = load_snap('HashMap')

    if params is None:
        params = HashMap()
    for key, value in kwargs.items():
        if value:
            params.put(key, value)
    return params

def build_read_params(file:str, bandNames:list=None, bname_match=True, useAdvancedOptions:bool=False):

    jpy = load_snap('jpy')

    band_names_arr = None
    mask_names_arr = None

    if bname_match:
        if bandNames:
            band_names_arr = jpy.array('java.lang.String', bandNames)
            mask_names_arr = jpy.array('java.lang.String', bandNames)
    else:
        if bandNames:
            default_bnames = get_default_bands(bandNames)
            band_names_arr = jpy.array('java.lang.String', default_bnames)
            default_mnames = get_default_masks(bandNames)
            mask_names_arr = jpy.array('java.lang.String', default_mnames)

    return _build_params(file=file, useAdvancedOptions=useAdvancedOptions, bandNames=band_names_arr, maskNames=mask_names_arr)

def build_apply_orbit_params(polyDegree:int=3, orbitType:str="Sentinel Precise (Auto Download)", continueOnFail:bool=False):

    jpy = load_snap('jpy')

    jint = jpy.get_type('java.lang.Integer')
    return _build_params(orbitType=orbitType, polyDegree=jint(polyDegree), continueOnFail=continueOnFail)

def build_calib_params(selectedPolarisations:list[str], outputSigmaBand=True, outputGammaBand:bool=False, outputBetaBand:bool=False,
                       outputImageInComplex:bool=False, outputImageScaleInDb=False):

    jpy = load_snap('jpy')

    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray, outputSigmaBand=outputSigmaBand, outputGammaBand=outputGammaBand, outputBetaBand=outputBetaBand,
                         outputImageInComplex=outputImageInComplex, outputImageScaleInDb=outputImageScaleInDb)

def build_terrain_correction_params(**kwargs):

    jpy = load_snap('jpy')
    double_type = jpy.get_type('java.lang.Double')

    if 'pixelSpacingInMeter' in kwargs and 'pixelSpacingInDegree' in kwargs:
        kwargs['pixelSpacingInMeter'] = double_type(kwargs['pixelSpacingInMeter'])
        kwargs['pixelSpacingInDegree'] = double_type(kwargs['pixelSpacingInDegree'])

    if 'sourceBandNames' in kwargs:
        kwargs['sourceBandNames'] = jpy.array('java.lang.String', kwargs['sourceBandNames'])

    return _build_params(**kwargs)

def build_thermal_noise_removal_params(selectedPolarisations:list[str]):

    jpy = load_snap('jpy')

    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray)

def build_clip_params(**kwargs):

    jpy = load_snap('jpy')

    assert kwargs['bandNames'], "bandNames must be provided"

    kwargs['bandNames'] = jpy.array('java.lang.String', kwargs['bandNames'])

    if 'tiePointGridNames' in kwargs:
        kwargs['tiePointGridNames'] = jpy.array('java.lang.String', kwargs['tiePointGridNames'])

    return _build_params(**kwargs)

def build_topsar_deburst_params(selectedPolarisations:list[str]):

    jpy = load_snap('jpy')

    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray)

def build_mosaic_params(geo_spec:dict, **kwargs):

    jpy = load_snap('jpy')

    OpVar = jpy.get_type('org.esa.snap.core.gpf.common.MosaicOp$Variable')
    vars = [OpVar(k, v) for k, v in kwargs['variables']]

    kwargs['variables'] = jpy.array('org.esa.snap.core.gpf.common.MosaicOp$Variable', vars)


    kwargs['westBound'] = geo_spec['ul_x'] + geo_spec['res_x'] / 2
    kwargs['eastBound'] = geo_spec['lr_x'] + geo_spec['res_x'] / 2

    kwargs['northBound'] = geo_spec['ul_y'] + geo_spec['res_y'] / 2
    kwargs['southBound'] = geo_spec['lr_y'] + geo_spec['res_y']

    kwargs['pixelSizeX'] = geo_spec['res_x']
    kwargs['pixelSizeY'] = -geo_spec['res_y']

    return _build_params(**kwargs)

def build_speckle_filter_params(**kwargs):

    jpy = load_snap('jpy')

    assert kwargs['sourceBandNames'], "sourceBandNames must be provided"
    int_type = jpy.get_type('java.lang.Integer')

    kwargs['sourceBandNames'] = jpy.array('java.lang.String', kwargs['sourceBandNames'])
    kwargs['filterSizeX'] = int_type(kwargs['filterSizeX'])
    kwargs['filterSizeY'] = int_type(kwargs['filterSizeY'])
    kwargs['dampingFactor'] = int_type(kwargs['dampingFactor'])
    kwargs['anSize'] = int_type(kwargs['anSize'])

    return _build_params(**kwargs)

def build_reproject_params(**kwargs):

    jpy = load_snap('jpy')

    assert kwargs['crs'], "crs must be provided"
    assert kwargs['resamplingName'] in ['nearest', 'bilinear', 'bicubic'], "Invalid resampling method"

    kwargs['resamplingName'] = kwargs['resamplingName'].title()

    double_type = jpy.get_type('java.lang.Double')
    if 'pixelSizeX' in kwargs and 'pixelSizeY' in kwargs:
        kwargs['pixelSizeY'] = kwargs['pixelSizeX'] = double_type(kwargs['pixelSizeX'])

    return _build_params(**kwargs)