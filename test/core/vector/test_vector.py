import unittest
from core.vector import Vector

class TestVector(unittest.TestCase):
    def setUp(self):
        self.vector_path = '/home/khw/__develope/tmp/etri/250414_ETRI/PREPROCESSING_LSBand/auxdata/contour_UTM52N.shp'
        self.raster = '/home/khw/__develope/tmp/etri/250414_ETRI/PREPROCESSING_LSBand/auxdata/contour_UTM52N.tif'

    def test_vector_creation(self):
        v = Vector(self.vector_path)

