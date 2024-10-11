import unittest
from osgeo import gdal
from core.util.gdal import mosaic_by_ds, copy_ds, unit_from_epsg

class TestCoreFuncs(unittest.TestCase):

    def test_mosaic(self):
        paths = [
            '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/S2A_MSIL1C_20230509T020651.0.tif',
            '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/S2A_MSIL1C_20230509T020651.1.tif',
        ]

        out_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/S2A_MSIL1C_20230509T020651.mosaic.tif'

        ds_list = []
        for path in paths:
            ds_list.append(gdal.Open(path))

        mosaic_ds = mosaic_by_ds(ds_list)
        copy_ds(mosaic_ds, "GTiff", is_bigtiff=False, compress=False, out_path=out_path)

    def test_get_unit(self):
        self.assertEqual(unit_from_epsg(4326)['unit_name'], 'degree')
        self.assertEqual(unit_from_epsg(5186)['unit_name'], 'metre')