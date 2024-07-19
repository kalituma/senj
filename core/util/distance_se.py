import numpy as np

def distance_se(doy):

    doy=float(doy)
    se = 1.00014-0.01671*np.cos(np.pi*(0.9856002831*doy-3.4532868)/180.)-0.00014*np.cos(2*np.pi*(0.9856002831*doy-3.4532868)/180.)
    return(se)