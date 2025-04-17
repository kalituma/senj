
#io
READ_OP = 'read'
WRITE_OP = 'write'
MULTI_WRITE_OP = 'multi_write'

#dim
STACK_OP = 'stack'
MOSAIC_OP = 'mosaic'
SUBSET_OP = 'subset'
SPLIT_OP = 'split'
RESAMPLE_OP = 'resample'
GCP_REPROJECT_OP = 'gcp_reproject'
SELECT_OP = 'select'

#pixel-wise
WARP_OP = 'warp'
CONVERT_OP = 'convert'
MINMAX_CLIP_OP = 'minmax_clip'

#s1, snap
APPLYORBIT_OP = 'apply_orbit'
CALIBRATE_OP = 'calibrate'
TERR_CORR_OP = 'terrain_correction'
THERM_NOISE_OP = 'thermal_noise_removal'
TOPSAR_DEBURST_OP = 'topsar_deburst'
SPECKLE_FILTER_OP = 'speckle_filter'

#cached
ATMOSCORR_OP = 'atmos_corr'
REV_REF_OP = 'rev_ref'
NL_DENOISING_OP = 'nl_mean_denoising'
NORMALIZE_OP = 'normalize'
BACK_COEF_OP = 'backscattering_coefficient'
CACHED_SPECKLE_FILTER_OP = 'cached_speckle_filter'
HIST_EQUAL_OP = 'histogram_equalization'
BAND_MATH_OP = 'bandmath'