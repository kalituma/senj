import numpy as np
from scipy.interpolate import interpn, RegularGridInterpolator
from scipy.ndimage import uniform_filter

from core.util import fillnan

def tiles_interp(data, xnew, ynew, smooth = False, kern_size=2, method='nearest', mask = None,
                 target_mask = None, target_mask_full = False, fill_nan = True, dtype = 'float32', use_rgi = False):

    if mask is not None: data[mask] = np.nan

    ## fill nans with closest value
    if fill_nan:
        cur_data = fillnan(data)
    else:
        cur_data = data*1.0

    dim = cur_data.shape
    if smooth: cur_data = uniform_filter(cur_data, size = kern_size)

    ## grid positions
    x = np.arange(0., dim[1], 1)
    y = np.arange(0., dim[0], 1)

    ## set up interpolator
    if use_rgi: ## use RGI
        rgi = RegularGridInterpolator((y,x), cur_data, bounds_error = False, fill_value = np.nan, method = method)
        if target_mask is None:
            znew = rgi((ynew[:,None], xnew[None, :]))
        else: ## limit to target mask
            vd = np.where(target_mask)
            if target_mask_full:
                znew = np.zeros((len(ynew), len(xnew))).astype(dtype)+np.nan
                znew[vd] = rgi((ynew[vd[0]], xnew[vd[1]]))
            else:
                znew = rgi((ynew[vd[0]], xnew[vd[1]]))
    else:
        if target_mask is None:
            znew = interpn((y,x), cur_data, (ynew[:,None], xnew[None, :]), method = method, bounds_error = False)
        else: ## limit to target mask
            vd = np.where(target_mask)
            if target_mask_full:
                znew = np.zeros((len(ynew), len(xnew))).astype(dtype)+np.nan
                znew[vd] = interpn((y,x), cur_data, (ynew[vd[0]], xnew[vd[1]]), method = method, bounds_error = False)
            else:
                znew = interpn((y,x), cur_data, (ynew[vd[0]], xnew[vd[1]]), method = method, bounds_error = False)

    ## to convert data type - scipy always returns float64
    if dtype is not None: znew = znew.astype(np.dtype(dtype))
    return(znew)
