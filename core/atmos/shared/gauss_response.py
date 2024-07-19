import numpy as np

def gauss_response(center, fwhm, step=1):
    wrange = (center - 1.5*fwhm, center + 1.5*fwhm)
    sigma = fwhm / (2*np.sqrt(2*np.log(2)))
    x = np.linspace(wrange[0], wrange[1], int(1+(wrange[1]-wrange[0])/step))
    y = np.exp(-((x-center)/sigma)**2 )
    return(x,y)
