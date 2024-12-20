import os, sys, fnmatch
from core.util import load_gdal

def read_band(file, idx = None, warp_to=None, warp_alg = 'near', # 'cubic', 'bilinear'
                 target_res=None, sub=None, gdal_meta = False, rpc_dem = None, targetAlignedPixels = False):

    gdal = load_gdal()

    close = False
    if type(file) == str:
        ds = gdal.Open(file)
        close = True ## close if we open file here
    elif type(file) == gdal.Dataset:
        ds = file
    else:
        print('{} not recognised'.format(file))
        return()

    nrows=ds.RasterYSize
    ncols=ds.RasterXSize

    if gdal_meta:
        try:
            md = ds.GetMetadata_Dict()
        except:
            md = {}

    if warp_to is None:
        if sub is None:
            if idx is not None:
                data = ds.GetRasterBand(idx).ReadAsArray()
            else:
                data = ds.ReadAsArray()
        else:
            cdiff = ncols - (sub[0]+sub[2])
            if cdiff < 0:
                sub[2]+=cdiff
            rdiff = nrows-(sub[1]+sub[3])
            if rdiff < 0:
                sub[3]+=rdiff
            if idx is not None:
                data = ds.GetRasterBand(idx).ReadAsArray(sub[0],sub[1],sub[2],sub[3])
            else:
                data = ds.ReadAsArray(sub[0],sub[1],sub[2],sub[3])
        if close: ds = None
    else:
        if len(warp_to) >= 2:
            dstSRS = warp_to[0] ## target projection

            ## target bounds in projected space
            if len(warp_to[1]) == 5:
                outputBounds = warp_to[1][0:4]
                outputBoundsSRS = warp_to[1][4]
            else:
                outputBounds = warp_to[1]
                outputBoundsSRS = dstSRS

            #targetAlignedPixels = True

            ## if we don't know target resolution, figure out from the outputBounds
            if target_res is None:
                xRes = None
                yRes = None
            else:
                if type(target_res) in (int, float):
                    xRes = target_res * 1
                    yRes = target_res * 1
                else:
                    xRes = target_res[0]
                    yRes = target_res[1]

            ## if given use target resolution
            if len(warp_to) >= 4:
                xRes = warp_to[2]
                yRes = warp_to[3]
            if (xRes is None) or (yRes is None): targetAlignedPixels = False

            ## use given warp algorithm
            if len(warp_to) >= 5:
                warp_alg = warp_to[4]

            ## add transformeroptions
            rpc = False
            RPCs = ds.GetMetadata('RPC')
            if len(RPCs) > 0: rpc = True
            transformerOptions = []
            if rpc_dem is not None: transformerOptions+=['RPC_DEM={}'.format(rpc_dem)]

            ## warp in memory and read dataset to array
            ## https://gdal.org/python/osgeo.gdal-module.html
            ds = gdal.Warp('', file,
                            xRes = xRes, yRes = yRes,
                            outputBounds = outputBounds, outputBoundsSRS = outputBoundsSRS,
                            dstSRS=dstSRS, targetAlignedPixels = targetAlignedPixels,
                            rpc = rpc, transformerOptions = transformerOptions,
                            format='VRT', resampleAlg=warp_alg)
            if idx is not None:
                data =  ds.GetRasterBand(idx).ReadAsArray()
            else:
                data = ds.ReadAsArray()
            if close: ds = None

    if gdal_meta:
        return(md, data)
    else:
        return(data)
