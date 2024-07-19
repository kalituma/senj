from osgeo import osr, gdal
import numpy as np
from core import atmos
from core.atmos.nc import nc_datasets, nc_data, nc_gatts, nc_write, nc_read_projection

def hillshade_nc(ncf, write_to_netcdf = False, options = [], # ['-combined']
                     dataset = 'dem', data = None):


    ## read NetCDF
    datasets = nc_datasets(ncf)
    if data is None:
        if dataset not in datasets:
            print('DEM not in {}'.format(ncf))
            return()
        data = nc_data(ncf, dataset)
    if 'hillshade' in datasets:
        hillshade = nc_data(ncf, 'hillshade')
        return(hillshade)

    ## read NetCDF global attributes
    gatts = nc_gatts(ncf)

    ## compute sun position
    centre_lon = np.nanmedian(nc_data(ncf, 'lon'))
    centre_lat = np.nanmedian(nc_data(ncf, 'lat'))
    sun = atmos.shared.sun_position(gatts['isodate'], centre_lon, centre_lat)
    alt = sun['elevation'][0]
    azi = sun['azimuth'][0]

    if False:
        ## get projection info and set up source dataset
        nc_projection = nc_read_projection(ncf)
        xrange = gatts['xrange']
        yrange = gatts['yrange']
        pixel_size = gatts['pixel_size']

        ## make WKT
        srs = osr.SpatialReference()
        srs.ImportFromProj4(gatts['proj4_string'])
        wkt = srs.ExportToWkt()
        ## make geotransform, add half a pixel for pixel centers
        trans = (xrange[0]+pixel_size[0]/2, pixel_size[0], 0.0, \
                 yrange[0]+pixel_size[1]/2, 0.0, pixel_size[1])

        ## in memory source dataset
        drv = gdal.GetDriverByName('MEM')
        ySrc,xSrc = data.shape
        source_ds = drv.Create('', xSrc, ySrc, 1,  gdal.GDT_Float32)
        source_ds.SetGeoTransform(trans)
        source_ds.SetProjection(wkt)
        ## put data in source_ds
        source_ds.GetRasterBand(1).WriteArray(data)
        source_ds.FlushCache()
        ## remove data
        data = None
    else:
        if 'projection_key' in gatts:
            source_ds = gdal.Translate('', 'NETCDF:"{}":{}'.format(ncf, 'dem'),
                                       format='MEM', creationOptions=None)


    ## compute hillshade
    ds = gdal.DEMProcessing('', source_ds, 'hillshade', options=options, format='MEM',  azimuth=azi, altitude=alt)
    hillshade = ds.ReadAsArray()
    ds = None
    source_ds = None

    if write_to_netcdf:
        nc_write(ncf, 'hillshade', hillshade)

    return(hillshade)
