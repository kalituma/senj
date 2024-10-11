import unittest

from netCDF4 import Dataset
from osgeo import gdal
from core.util import identify_product, identify_nc, ProductType

class TestCoreFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.cdom_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/CDOM/2021/5/GK2B_GOCI2_L2_20210531_231530_LA_S000_CDOM.nc'
        self.rsr_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/RSR/2021/5/GK2B_GOCI2_L2_20210531_231530_LA_S000_AC.nc'
        self.smap_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/SMAP/2021/5/SMAP_L3_SSS_20210531_8DAYS_V5.0.nc.nc4'
        self.sst = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/SST/2021/5/KHOA_SST_L4_Z003_D01_WGS001K_U20210531.nc'

    def test_indentify(self):

        product_type, _ = identify_product(self.cdom_path)
        self.assertEqual(product_type, ProductType.GOCI_CDOM)

        product_type, _ = identify_product(self.rsr_path)
        self.assertEqual(product_type, ProductType.GOCI_AC)

        product_type, _ = identify_product(self.smap_path)
        self.assertEqual(product_type, ProductType.SMAP)

        product_type, _ = identify_product(self.sst)
        self.assertEqual(product_type, ProductType.KHOA_SST)

    def test_nc_band_list(self):

        cdom = Dataset(self.cdom_path)
        rrs = Dataset(self.rsr_path)
        smap = Dataset(self.smap_path)
        sst = Dataset(self.sst)

        print()

