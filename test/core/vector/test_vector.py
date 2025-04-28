import unittest
from osgeo import gdal

from core.util.gdal import create_dem, create_slope

from core.logic import Context
from core.vector import Vector
from core.raster.funcs.reader import TifGdalReader
from core.vector.funcs.reader import ShapeGdalReader
from core.operations import VectorClip


class TestVector(unittest.TestCase):
    def setUp(self):
        self.vector_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PREPROCESSING_LSBand/auxdata/contour_UTM52N.shp'
        self.raster_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PREPROCESSING_LSBand/auxdata/src_UTM52N.tif'
        self.ref_dem_path = "/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/etri_example_updated/OUTPUTDATA/SnowRiskDamageArea_Preprocessing/dem_clipped.tif"
    
    def test_vector_clipping(self):
        context = Context(None)

        with self.subTest('creating raster'):
            rreader = TifGdalReader()
            r = rreader.read(self.raster_path)
            print(r.envelope_geom)

        with self.subTest('clipping vector'):
            vreader = ShapeGdalReader()
            v = vreader.read(self.vector_path)
            new_v = Vector.like(v)
            clip_op = VectorClip(r.bounds)
            clipped_v = clip_op(v, context)
            self.assertEqual(clipped_v.bounds, r.bounds)

        with self.subTest("making dem"):
            out_path = "/vsimem/memory_grid"
            clipped_dem = create_dem(clipped_v.raw, out_ds=out_path, out_bounds=r.bounds, res=2.8, column_name='CONT')
            ds = gdal.Open(self.ref_dem_path)

        with self.subTest("making slope"):
            out_path = "/vsimem/memory_slope"
            slope = create_slope(clipped_dem, out_ds=out_path)
            print()
    
    def test_intersects_and_merge(self):
        shape_path = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PRODUCT_LandslideDamageArea/auxdata/mask_split_by_grid'
        bounds_csv = '/home/airs_khw/mount/d_drive/__develope/temp/_done/2024/etri/_product/250414_ETRI/PRODUCT_LandslideDamageArea/auxdata/grid_split_xy.csv'

        import pandas as pd

        df = pd.read_csv(bounds_csv)
        for index, row in df.iterrows():
            x = row['x']
            y = row['y']
            print(x, y)
        
