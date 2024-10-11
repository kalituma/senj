OUT_TYPE_MAP = {
    'tif': 'GeoTIFF',
    'bigtif': 'GeoTIFF-BigTIFF',
    'dim': 'BEAM-DIMAP'
}

EXT_MAP = {
    'gdal': 'tif',
    'snap': ['dim', 'tif']
}

MODULE_EXT_MAP = {
    'gdal' : ['tif', 'xml'],
    'snap' : ['dim', 'tif', 'safe', 'xml'],
    'netcdf' : ['nc', 'nc4']
}


LOAD_IMAGES_ALLOWED_EXT = ['tif', 'dim', 'xml', 'safe', 'nc', 'nc4']