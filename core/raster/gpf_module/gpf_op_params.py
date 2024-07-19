from esa_snappy import HashMap, jpy

from core.raster.gpf_module import get_default_bands, get_default_masks

def _build_params(params: HashMap=None, **kwargs):
    if params is None:
        params = HashMap()
    for key, value in kwargs.items():
        if value:
            params.put(key, value)
    return params

def build_read_params(file:str, bandNames:list=None, bname_match=True, useAdvancedOptions:bool=False):
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

    jint = jpy.get_type('java.lang.Integer')
    return _build_params(orbitType=orbitType, polyDegree=jint(polyDegree), continueOnFail=continueOnFail)

def build_calib_params(selectedPolarisations:list[str], outputSigmaBand=True, outputGammaBand:bool=False, outputBetaBand:bool=False,
                       outputImageInComplex:bool=False, outputImageScaleInDb=False):
    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray, outputSigmaBand=outputSigmaBand, outputGammaBand=outputGammaBand, outputBetaBand=outputBetaBand,
                         outputImageInComplex=outputImageInComplex, outputImageScaleInDb=outputImageScaleInDb)

def build_terrain_correction_params(sourceBandNames:list[str], imgResamplingMethod:str, demName:str,
                                    demResamplingMethod:str, pixelSpacingInMeter:float, pixelSpacingInDegree:float,
                                    mapProjection:str, saveDem:bool=False):
    double_type = jpy.get_type('java.lang.Double')
    source_bands = jpy.array('java.lang.String', sourceBandNames)
    return _build_params(sourceBands=source_bands, imgResamplingMethod=imgResamplingMethod, demName=demName, demResamplingMethod=demResamplingMethod,
                         pixelSpacingInMeter=double_type(pixelSpacingInMeter), pixelSpacingInDegree=double_type(pixelSpacingInDegree), mapProjection=mapProjection,
                         saveDEM=saveDem)

def build_thermal_noise_removal_params(selectedPolarisations:list[str]):
    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray)

def build_subset_params(**kwargs):

    assert kwargs['bandNames'], "bandNames must be provided"

    kwargs['bandNames'] = jpy.array('java.lang.String', kwargs['bandNames'])

    if 'tiePointGridNames' in kwargs:
        kwargs['tiePointGridNames'] = jpy.array('java.lang.String', kwargs['tiePointGridNames'])

    return _build_params(**kwargs)

def build_topsar_deburst_params(selectedPolarisations:list[str]):
    polarArray = jpy.array('java.lang.String', selectedPolarisations)
    return _build_params(selectedPolarisations=polarArray)

def build_speckle_filter_params(**kwargs):
    assert kwargs['sourceBandNames'], "sourceBandNames must be provided"
    assert kwargs['filter'] in [BOXCAR, MEDIAN, FROST, GAMMA_MAP, LEE_SPECKLE, LEE_REFINED, LEE_SIGMA, IDAN, MEAN_SPECKLE], "Invalid filter type"
    int_type = jpy.get_type('java.lang.Integer')

    kwargs['sourceBandNames'] = jpy.array('java.lang.String', kwargs['sourceBandNames'])
    kwargs['filterSizeX'] = int_type(kwargs['filterSizeX'])
    kwargs['filterSizeY'] = int_type(kwargs['filterSizeY'])
    kwargs['dampingFactor'] = int_type(kwargs['dampingFactor'])
    kwargs['anSize'] = int_type(kwargs['anSize'])

    return _build_params(**kwargs)