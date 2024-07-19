import numpy as np
from matplotlib.colors import Normalize

def percentile_norm(img:np.ndarray, p_low:float=2, p_high:float=98):

    low, high = np.percentile(img, (p_low, p_high))
    pnorm = Normalize(vmin=low, vmax=high, clip=True)
    return pnorm(img)