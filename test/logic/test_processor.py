import os
import unittest
from functools import partial
from pathlib import Path

from core.config import expand_var
from core.util import sort_by_pattern, OperationTypeError
from core.raster import Raster
from core.logic import Context
from core.logic.executor import ProcessingExecutor
from core.logic.processor import FileProcessor, LinkProcessor
from core.operations import Read, Write, Stack

class TestProcessor(unittest.TestCase):
    def setUp(self) -> None:
        self.tif_src_1 = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'tif', 's1', 'gdal', 'src_1'))
        self.tif_src_2 = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'tif', 's1', 'gdal', 'src_2'))
        self.safe_src_1 = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'safe', 's1', 'list'))
        self.name_date_pattern = '([12]\d{3}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])T(?:0[0-9]|1[0-9]|2[0-3])(?:[0-5][0-9])(?:[0-5][0-9]))'
        self.date_pattern = '%Y%m%dT%H%M%S'

    def test_file_processor(self):
        result_target = ['$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_0.tif', '$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_1.tif',
                         '$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_10.tif','$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_11.tif',
                         '$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_12.tif','$PROJECT_PATH/data/test/tif/s1/gdal/src_1/terrain_corrected_2.tif']
        f_processor = FileProcessor(proc_name="processor_1", path=self.tif_src_1, pattern='*.tif', sort=None, splittable=True)
        with self.subTest('test preprocess'):
            for i, f_path in enumerate(f_processor.preprocess()):
                result_target[i] = expand_var(result_target[i])
                self.assertEqual(f_path, result_target[i])

        sort_func = lambda x: int(x.stem.split('_')[-1])
        f_processor = FileProcessor(proc_name="processor_2", path=self.tif_src_1, pattern='*.tif', sort={'func':sort_func}, splittable=True)
        result_target = sorted(result_target, key=lambda x: int(x.split('_')[-1].split('.')[0]))
        with self.subTest('test preprocess with sort'):
            for i, f_path in enumerate(f_processor.preprocess()):
                self.assertEqual(f_path, result_target[i])

        result_target = ['$PROJECT_PATH/data/test/safe/s1/list/S1B_IW_SLC__1SDV_20180808T213153_20190807T213220_017485_020E22_1063.SAFE',
                         '$PROJECT_PATH/data/test/safe/s1/list/S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1062.SAFE',
                         '$PROJECT_PATH/data/test/safe/s1/list/S1B_IW_SLC__1SDV_20190808T213153_20190807T213220_017485_020E22_1061.SAFE']

        sort_func = partial(sort_by_pattern, str_pattern=self.name_date_pattern, date_pattern=self.date_pattern)
        f_processor = FileProcessor(proc_name="processor_safe_1", path=self.safe_src_1, pattern='*.SAFE', sort={'func':sort_func}, splittable=True)
        with self.subTest('test preprocess with SAFE file'):
            for i, f_path in enumerate(f_processor.preprocess()):
                result_target[i] = expand_var(result_target[i])
                self.assertEqual(f_path, result_target[i])

        result_target = sorted(result_target, key=lambda x: int(x.split('_')[-1].split('.')[0]))
        sort_func = lambda x: int(x.stem.split('_')[-1].split('.')[0])
        f_processor = FileProcessor(proc_name="processor_safe_1", path=self.safe_src_1, pattern='*.SAFE', sort={'func': sort_func}, splittable=True)
        with self.subTest('test preprocess with SAFE file using different sort function'):
            for i, f_path in enumerate(f_processor.preprocess()):
                self.assertEqual(f_path, result_target[i])

    def test_file_processor_fail(self):
        with self.subTest('test preprocess with non-exist path'):
            f_processor = FileProcessor(proc_name="processor_1", path='non_exist', pattern='*.tif', sort=None, splittable=True)
            with self.assertRaises(AssertionError):
                for f_path in f_processor.preprocess():
                    pass

        with self.subTest('test preprocess with none matched pattern'):
            f_processor = FileProcessor(proc_name="processor_1", path=self.tif_src_1, pattern='*.jpg', sort=None, splittable=True)
            with self.assertRaises(AssertionError):
                for f_path in f_processor.preprocess():
                    pass

    def test_file_processor_op(self):
        with self.subTest('construct processor with operations'):
            f_processor = FileProcessor(proc_name="processor_1", path=self.tif_src_1, pattern='*.tif', sort=None, splittable=True).add_op(
                Read(module='snap')
            )
            file_size = len(list(Path(self.tif_src_1).rglob('*.tif')))
            cnt = 0
            for f_path in f_processor.preprocess():
                result = f_processor.process(f_path, Context())
                self.assertTrue(isinstance(result, Raster))
                cnt += 1
            self.assertEqual(cnt, file_size)

    def test_file_processor_op_fail(self):
        with self.subTest('test add_op with unsupported operation'):
            f_processor = FileProcessor(proc_name="processor_1", path=self.tif_src_1, pattern='*.tif', sort=None, splittable=True)
            with self.assertRaises(OperationTypeError):
                f_processor.add_op(Write(module='snap', path='a.tif'))

    def test_link_processor(self):
        cxt = Context()
        f_processor_1 = FileProcessor(proc_name="processor_1", path=self.tif_src_1, pattern='*.tif', sort=None,splittable=True).add_op(Read(module='snap'))
        f_processor_2 = FileProcessor(proc_name="processor_1", path=self.tif_src_2, pattern='*.tif', sort=None,splittable=True).add_op(Read(module='snap'))
        l_processor = LinkProcessor(proc_name="link_processor", processors=[f_processor_1, f_processor_2]).add_op(Stack())
        executor = ProcessingExecutor(cxt)
        l_processor.set_executor(executor)
        with self.subTest('test link processor'):
            for raster_list in l_processor.preprocess():
                self.assertEqual(len(raster_list), 2)