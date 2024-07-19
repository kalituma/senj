import os, sys

def lutnc_import(lutnc):

    ## read dataset from NetCDF
    try:
        from netCDF4 import Dataset
        nc = Dataset(lutnc)
        meta=dict()
        for attr in nc.ncattrs():
            attdata = getattr(nc,attr)
            if isinstance(attdata,str): attdata = attdata.split(',')
            meta[attr]=attdata

        ## read lut
        datasets = list(nc.variables.keys())
        if (len(datasets) == 1) & (datasets == ['lut']):
            ## generic lut
            lut = nc.variables['lut'][:]
        else:
            ## sensor specific lut with multiple luts (per band)
            lut = {}
            for dataset in datasets:
                lut[dataset] = nc.variables[dataset][:]
        nc.close()
    except:
        print(sys.exc_info()[0])
        print('Failed to open LUT {} data from NetCDF'.format(os.path.basename(lutnc)))
        print('File not found {}'.format(lutnc))
        sys.exit(1)

    return(lut,meta)
