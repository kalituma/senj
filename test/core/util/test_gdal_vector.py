import unittest

class TestGdalVector(unittest.TestCase):

    def setUp(self):
        self.map_csv = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PRODUCT_LandslideDamageArea/auxdata/grid_split_xy.csv'
        self.mask_split_dir = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PRODUCT_LandslideDamageArea/auxdata/mask_split_by_grid'

    def test_clip_vector(self):
        pass
