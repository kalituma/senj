import os
import unittest

from os.path import expandvars as expand_var
from core.util import ModuleType
from core.raster.funcs.reader import TifGdalReader, SafeGdalReader, SnapReader


class TestGdalReader(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))

    def test_read_tif(self):
        
        with self.subTest('capella'):
            tif_path = os.path.join(self.test_data_root, 'tif', 'cp', 'CAPELLA_C06_SM_GEC_HH_20220904051748_20220904051752', 'CAPELLA_C06_SM_GEC_HH_20220904051748_20220904051752.tif' )
            reader = TifGdalReader(tif_path)
            raster = reader.read_data()

        with self.subTest('cas500'):
            tif_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/CAS500/C1_20230409020925_11372_00447619_L2G/C1_20230409020925_11372_00447619_L2G_B.tif'
            reader = TifGdalReader(tif_path)
            raster = reader.read_data()

        with self.subTest('k3'):
            tif_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/K3/K3_20190605041141_37608_09371263_L1G/K3_20190605041141_37608_09371263_L1G_B.tif'
            reader = TifGdalReader(tif_path)
            raster = reader.read_data()

        with self.subTest('k3a'):
            tif_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/K3A/K3A_20190412041629_22339_00232884_L1G/K3A_20190412041629_22339_00232884_L1G_B.tif'
            reader = TifGdalReader(tif_path)
            raster = reader.read_data()
            print()

    def test_read_safe_snap(self):

        with self.subTest('safe s1'):
            s1_grdh_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
            reader = SnapReader(s1_grdh_path)
            raster = reader.read_data()
            print(raster.meta_dict)
            s1_slc_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
            reader = SnapReader(s1_slc_path)
            raster = reader.read_data()
            print(raster.meta_dict)
        
        with self.subTest('safe s2'):
            s2_path = os.path.join(self.test_data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
            reader = SnapReader(s2_path)
            raster = reader.read_data()
            print(raster.meta_dict)

    def test_read_dim_snap(self):

        with self.subTest('dim s1'):
            s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
            reader = SnapReader(s1_dim_path)
            raster = reader.read_data()
            print(raster.meta_dict)
            
        with self.subTest('dim s2'):
            s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
            reader = SnapReader(s2_dim_path)
            raster = reader.read_data()
            print(raster.meta_dict)

    def test_read_safe_gdal(self):
        with self.subTest('safe gdal s1'):
            safe_path = "/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/S2/S2A_MSIL2A_20230412T021531_N0509_R003_T52SBF_20230412T070105.SAFE"
            reader = SafeGdalReader(safe_path)
            raster = reader.read(['B02', 'B03', 'B04', 'B08'], res='10m')
            print(raster.meta_dict)


    def test_read_gdal(self):
        from core.raster.funcs.reader import NcReader, GribGdalReader
        
        with self.subTest('gk2a'):
            nc_path = "/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/GK2A/gk2a_ami_le2_scsi_ko020lc_201912260600.nc"
            reader = NcReader(nc_path)
            raster = reader.read_data()
            print(raster.meta_dict)

        with self.subTest('ldaps'):
            grib_path = "/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/INPUTDATA/LDAPS/l015_v070_erlo_unis_h000.2019122606.gb2"
            reader = GribGdalReader(grib_path)
            raster = reader.read_data()
            print(raster.meta_dict)
