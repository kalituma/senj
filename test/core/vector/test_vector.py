import unittest
from osgeo import gdal

from core.util import expand_var
from core.util.gdal import create_dem, create_slope

from core.logic import Context
from core.vector import Vector
from core.raster.funcs.reader import TifGdalReader
from core.vector.funcs.reader import ShapeGdalReader
from core.operations import VectorClip

class TestVector(unittest.TestCase):
    def setUp(self):
        self.vector_path = expand_var('$PROJECT_PATH/data/etri/ADDDATA/LandSlide/mask_split_by_grid/30001.shp')
        self.raster_path = expand_var('$PROJECT_PATH/data/etri/OUTPUTDATA/LandslideDamageArea_Preprocessing/src_UTM52N.tif')
        self.ref_dem_path = expand_var('$PROJECT_PATH/data/etri/OUTPUTDATA/LandslideDamageArea_Preprocessing/dem_clipped.tif')
    
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
        import os
        import pandas as pd
        from osgeo import ogr
        from core.raster import Raster
        from core.raster.funcs.reader import TifGdalReader
        from core.vector.funcs.reader import ShapeGdalReader
        from core.vector.funcs.writer import ShapeGdalWriter
        from core.vector.funcs import VectorClipper, VectorMerger
        from core.util import ModuleType

        shape_path = expand_var('$PROJECT_PATH/data/etri/ADDDATA/LandSlide/mask_split_by_grid')
        bounds_csv = expand_var('$PROJECT_PATH/data/etri/ADDDATA/LandSlide/grid_split_xy.csv')
        clipped_shape_path = expand_var('$PROJECT_PATH/data/etri/OUTPUTDATA/LandslideDamageArea_Preprocessing/clipped_merged_shape.shp')
        dem_path = expand_var('$PROJECT_PATH/data/etri/OUTPUTDATA/LandslideDamageArea_Preprocessing/dem_clipped.tif')
        slope_path = expand_var('$PROJECT_PATH/data/etri/OUTPUTDATA/LandslideDamageArea_Preprocessing/slope_clipped.tif')

        rreader = TifGdalReader()
        ref_raster = rreader.read(self.raster_path)

        df = pd.read_csv(bounds_csv)
        clipped_v = []
        for index, row in df.iterrows():
            bbox_wkt = f"POLYGON(({row['BL_X']} {row['BL_Y']}, {row['UR_X']} {row['BL_Y']}, \
                    {row['UR_X']} {row['UR_Y']}, {row['BL_X']} {row['UR_Y']}, {row['BL_X']} {row['BL_Y']}))"
            bbox_geom = ogr.CreateGeometryFromWkt(bbox_wkt)
            intersection_geom = bbox_geom.Intersection(ref_raster.envelope_geom)

            if not intersection_geom.IsEmpty():
                grid_num = int(row['Num'])
                mask_split_shp_file = os.path.join(shape_path, f"{grid_num}.shp")
                vreader = ShapeGdalReader()
                v = vreader.read(mask_split_shp_file)
                clip_op = VectorClipper.clip(v, ref_raster.envelope_geom)
                clipped_v.append(clip_op)
        
        merged_v = VectorMerger.merge(clipped_v)
        
        raster = Raster.from_raster(ref_raster)
        clipped_dem = create_dem(merged_v.raw, out_ds=dem_path, out_bounds=merged_v.bounds, res=2.8, column_name='CONT')
        slope = create_slope(clipped_dem, out_ds=slope_path)


