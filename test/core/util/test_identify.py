import unittest

from netCDF4 import Dataset
from osgeo import gdal
from core.util import ProductType
from core.util.identify import identify_product, identify_nc

class TestCoreFuncs(unittest.TestCase):
    def setUp(self) -> None:
        # nc
        self.cdom_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/CDOM/2021/5/GK2B_GOCI2_L2_20210531_231530_LA_S000_CDOM.nc'
        self.rsr_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/RRS/2021/5/GK2B_GOCI2_L2_20210531_231530_LA_S000_AC.nc'
        self.smap_path = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/SMAP/2021/5/SMAP_L3_SSS_20210531_8DAYS_V5.0.nc.nc4'
        self.sst = '/home/airs_khw/mount/expand/data/elecocean/salinity/input/SST/2022/5/KHOA_SST_L4_Z003_D01_WGS001K_U20220501.nc'
        self.gk2a = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/GK2A/gk2a_ami_le2_scsi_ko020lc_201912260600.nc'

        # gb2
        self.ldaps = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/LDAPS/l015_v070_erlo_unis_h000.2019122606.gb2'

        # tif
        self.cas500_b = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/CAS500/C1_20230409020925_11372_00447619_L2G/C1_20230409020925_11372_00447619_L2G_B.tif'
        self.k3 = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/K3/K3_20210107043146_46111_09381273_L1G/K3_20210107043146_46111_09381273_L1G_B.tif'
        self.k3a = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/K3A/K3A_20190412041629_22339_00232884_L1G/K3A_20190412041629_22339_00232884_L1G_B.tif'

    def test_identify_tif(self):
        with self.subTest(msg='CAS500'):
            product_type, _ = identify_product(self.cas500_b)
            self.assertEqual(product_type, ProductType.CA)

        with self.subTest(msg='K3'):
            product_type, _ = identify_product(self.k3)
            self.assertEqual(product_type, ProductType.K3)

        with self.subTest(msg='K3A'):
            product_type, _ = identify_product(self.k3a)
            self.assertEqual(product_type, ProductType.K3)

    def test_identify_nc(self):

        with self.subTest(msg='CDOM'):
            product_type, _ = identify_product(self.cdom_path)
            self.assertEqual(product_type, ProductType.GOCI_CDOM)

        with self.subTest(msg='RRS'):
            product_type, _ = identify_product(self.rsr_path)
            self.assertEqual(product_type, ProductType.GOCI_AC)

        with self.subTest(msg='SMAP'):
            product_type, _ = identify_product(self.smap_path)
            self.assertEqual(product_type, ProductType.SMAP)

        with self.subTest(msg='SST'):
            product_type, _ = identify_product(self.sst)
            self.assertEqual(product_type, ProductType.KHOA_SST)

        with self.subTest(msg='GK2A'):
            product_type, _ = identify_product(self.gk2a)
            self.assertEqual(product_type, ProductType.GK2A)

    def test_identify_ldaps(self):
        with self.subTest(msg='LDAPS'):
            product_type, _ = identify_product(self.ldaps)
            self.assertEqual(product_type, ProductType.LDAPS)



