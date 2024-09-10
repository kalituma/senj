import os
import unittest
from pathlib import Path
from core.raster import RasterType, Raster
from core.raster.funcs import update_meta_band_map, get_epsg, load_raster, load_images_paths, create_meta_dict, init_bname_index_in_meta, set_raw_metadict
from core.util import identify_product, parse_meta_xml, read_pickle, expand_var, ProductType, get_btoi_from_tif
from core.util.gdal import load_raster_gdal, mosaic_by_file_paths
from core.util.snap import load_raster_gpf, mosaic_gpf, rename_bands

from core.logic.context import Context
from core.operations import Read, Write, Split, MultiWrite

class TestRasterFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_without_meta = os.path.join(self.test_data_root, 'tif', 'no_meta', 'out_0_read.tif')
        self.s2_without_meta_head = os.path.join(self.test_data_root, 'tif', 'no_meta_with_tif_head', 'read_select_write.0.tif')

        self.s2_dim = os.path.join(self.test_data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s2_tif = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')

        self.s1_safe_grdh_path = os.path.join(self.test_data_root, 'safe', 's1',
                                              'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_safe_slc_path = os.path.join(self.test_data_root, 'safe', 's1',
                                             'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.test_data_root, 'safe', 's2',
                                         'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

        self.wv_xml_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL','19APR04021253-M2AS-014493935010_01_P001.XML')
        self.wv_tif_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF')

        self.ge_tif_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF')
        self.ge_xml_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS-014493907010_01_P001.XML')

        self.ps_tif_path = os.path.join(self.test_data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_clip.tif')
        self.ps_xml_path = os.path.join(self.test_data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_metadata_clip.xml')

        self.s1_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's1', 'snap', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's2', 'snap',
                                             'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.s1_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's1', 'gdal', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')


    def test_read_and_band_map(self):
        context = Context()
        with self.subTest('read tif not having meta using snap'):
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            self.assertEqual(result_raster.get_band_names(), [f'band_{index}' for index in range(1, len(result_raster.raw.getBands()) + 1)])

        with self.subTest('read dim file'):
            result_raster = Read(module='snap')(self.s2_dim, context)
            self.assertEqual(result_raster.get_band_names(), list(result_raster._index_to_band.values()))
            meta_dict = result_raster.meta_dict
            new_meta = update_meta_band_map(meta_dict, [1, 2, 3])
            result_raster.meta_dict = new_meta
            self.assertEqual(result_raster._index_to_band, new_meta['index_to_band'])

    def test_get_epsg(self):
        context = Context()
        s2_snap = Read(module='snap')(self.s2_dim, context)
        s2_gdal = Read(module='gdal')(self.s2_tif, context)
        self.assertEqual(get_epsg(s2_snap), 32652)
        self.assertEqual(get_epsg(s2_gdal), 32652)

    def test_load_raster_dim(self):

        # Write(module='snap')(s1_dim_raster, 'test.tif', Context())
        self.load_raster_reimpl(self.s1_dim_path, in_module='snap')
        self.load_raster_reimpl(self.s2_dim_path, in_module='snap')
        self.load_raster_reimpl(self.s1_safe_grdh_path, in_module='snap')

    def test_load_raster_tif_with_snap(self):
        self.load_raster_reimpl(self.s1_tif_snap_path, in_module='snap')
        self.load_raster_reimpl(self.s2_tif_snap_path, in_module='gdal')
        self.load_raster_reimpl(self.s1_tif_gdal_path, in_module='snap')
        self.load_raster_reimpl(self.s2_tif_gdal_path, in_module='gdal')
    def test_load_raster_wv(self):
        self.load_raster_reimpl(self.wv_xml_path, in_module='snap')
        self.load_raster_reimpl(self.wv_tif_path, in_module='snap')
        self.load_raster_reimpl(self.wv_xml_path, in_module='gdal')
        self.load_raster_reimpl(self.ge_xml_path, in_module='snap')
        self.load_raster_reimpl(self.ge_xml_path, in_module='gdal')
        self.load_raster_reimpl(self.ps_xml_path, in_module='snap')
        self.load_raster_reimpl(self.ps_tif_path, in_module='gdal')

    def test_load_raster_ps(self):
        self.load_raster_reimpl(self.s2_without_meta, in_module='snap')
        self.load_raster_reimpl(self.s2_without_meta, in_module='gdal')
        self.load_raster_reimpl(self.s2_without_meta_head, in_module='snap')
        self.load_raster_reimpl(self.s2_without_meta_head, in_module='gdal')

    def load_raster_reimpl(self, path, in_module):
        in_raster = Raster(path)
        in_raster.module_type = in_module
        in_module = RasterType.from_str(in_module)

        product_type, meta_path = identify_product(path)

        if product_type == ProductType.WV:  # to merge tiles for WorldView, in_path should be the xml file
            in_raster.path = path = meta_path

        image_paths = load_images_paths(path, product_type)

        update_meta_bounds = False
        if in_raster.module_type == RasterType.GDAL:
            if len(image_paths) > 1:
                raw = mosaic_by_file_paths(image_paths)
                update_meta_bounds = True
            else:
                datasets = load_raster_gdal(image_paths)
                raw = datasets[0]

        elif in_raster.module_type == RasterType.SNAP:
            datasets = load_raster_gpf(image_paths)

            if len(datasets) > 1:
                raw = mosaic_gpf(datasets)
                update_meta_bounds = True
            else:
                raw = datasets[0]
        else:
            raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

        band_to_index = None
        if Path(path).suffix[1:].lower() == 'tif':
            band_to_index = get_btoi_from_tif(path)

        meta_dict = create_meta_dict(raw, product_type, in_module, path, update_meta_bounds=update_meta_bounds)
        meta_dict = init_bname_index_in_meta(meta_dict, raw, product_type=product_type, module_type=in_raster.module_type, band_to_index=band_to_index)
        if meta_dict:
            band_to_index = None
        in_raster = set_raw_metadict(in_raster, raw=raw, meta_dict=meta_dict, product_type=product_type)
        in_raster = in_raster.update_index_bnames(band_to_index)

        if in_raster.module_type == RasterType.SNAP:
            in_raster.raw = rename_bands(in_raster.raw, band_names=in_raster.get_band_names())

        return in_raster