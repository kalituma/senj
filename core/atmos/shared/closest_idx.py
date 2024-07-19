def closest_idx(xlist, xval):
    idx,xret = min(enumerate(xlist), key=lambda x: abs(float(x[1])-float(xval)))
    return(idx,xret)