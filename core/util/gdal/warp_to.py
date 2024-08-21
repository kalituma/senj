from osgeo import osr,gdal

gdal_types = {
    'uint': gdal.GDT_UInt16,
    'int': gdal.GDT_Int16,
    'float': gdal.GDT_Float32,
}

def warp_to(source, data, warp_to, rpc_dem=None, type='float'):

    xSrc = int(source['xdim'])
    ySrc = int(source['ydim'])
    gt = source['ul_x'], source['pixel_size'], 0.0,\
         source['ul_y'], 0.0, -source['pixel_size']
    if 'Wkt' in source:
        wkt = source['Wkt']
        epsg = None
    else:
        wkt = None
        epsg = source['epsg']

    srs = osr.SpatialReference()
    if wkt is not None:
        srs.ImportFromWkt(wkt)
    elif epsg is not None:
        srs.ImportFromEPSG(epsg)
        wkt = srs.ExportToWkt()
    else:
        print('Failed to determine projection.')
        return

    ## in memory source dataset based chosen band
    drv = gdal.GetDriverByName('MEM')
    source_ds = drv.Create('', xSrc, ySrc, 1, gdal_types[type])
    source_ds.SetGeoTransform(gt)
    source_ds.SetProjection(wkt)

    ## put data in source_ds
    source_ds.GetRasterBand(1).WriteArray(data)
    source_ds.FlushCache()

    warp_to_region = warp_to

    ## warp the data
    if True:
        dstSRS = warp_to_region[0] ## target projection
        ## target bounds in projected space
        if len(warp_to_region[1]) == 5:
            outputBounds = warp_to_region[1][0:4]
            outputBoundsSRS = warp_to_region[1][4]
        else:
            outputBounds = warp_to_region[1]
            outputBoundsSRS = dstSRS
        targetAlignedPixels = True
        # targetAlignedPixels = False

        target_res = None
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
        if len(warp_to_region) >= 4:
            xRes = warp_to_region[2]
            yRes = warp_to_region[3]
        #if (xRes is None) or (yRes is None): targetAlignedPixels = False

        ## use given warp algorithm
        if len(warp_to_region) >= 5:
            warp_alg = warp_to_region[4]

        ## add transformeroptions
        rpc = False

        transformerOptions = []
        if rpc_dem is not None: transformerOptions+=['RPC_DEM={}'.format(rpc_dem)]

        ## warp in memory and read dataset to array
        ## https://gdal.org/python/osgeo.gdal-module.html
        #ds = gdal.Warp('', source_ds,
        #                xRes = xRes, yRes = yRes,
        #                outputBounds = outputBounds, outputBoundsSRS = outputBoundsSRS,
        #                dstSRS=dstSRS, targetAlignedPixels = targetAlignedPixels,
        #                format='VRT', resampleAlg=warp_alg)

        ds = gdal.Warp('', source_ds,
                        xRes = xRes, yRes = yRes,
                        outputBounds = outputBounds, outputBoundsSRS = outputBoundsSRS,
                        dstSRS=dstSRS, targetAlignedPixels = targetAlignedPixels,
                        rpc = rpc, transformerOptions = transformerOptions,
                        format='VRT', resampleAlg=warp_alg)

        data = ds.ReadAsArray()
        ds = None
    source_ds = None
    return(data)
