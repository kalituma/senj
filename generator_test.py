import numpy as np

from core.operations import Read, Stack, Write, Subset
from core.operations.cached import NLMeanDenoising
from core.operations.s1 import ApplyOrbit, Calibrate, TerrainCorrection, ThermalNoiseRemoval, TopsarDeburst, SpeckleFilter


from core.logic import Context
from core.logic.processor import LinkProcessor, FileProcessor
from core.logic.executor import ProcessingExecutor

def merge_tif():
    path_1 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/format/s2/B4_B3_B2_subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.tif'
    path_2 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/format/s2/B4_B3_B2_subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.1.tif'
    path_3 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/format/s2/B4_B3_B2_subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.2.tif'

    out_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/merged/s2/s2.tif'

    read_1 = FileProcessor('file_1', path_1) \
        .add_op(Read(module='gdal'))
    read_2 = FileProcessor('file_1', path_2) \
        .add_op(Read(module='gdal'))
    read_3 = FileProcessor('file_1', path_3) \
        .add_op(Read(module='gdal'))

    merge_1 = LinkProcessor('merge_1', [read_1, read_2, read_3]) \
        .add_op(Stack(bands=[[1], [1,2], [1,3]])) \
        .add_op(Write(path=out_path, module='gdal', out_ext='tif'))


    ctx = Context()
    # write_1 = LinkProcessor('write_1', [read_1])

    file_executor_1 = ProcessingExecutor(ctx)
    merge_1.set_executor(file_executor_1)
    w_gen_1 = merge_1.execute()
    for i, x in enumerate(w_gen_1):
        print()

def merge():
    path_1 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/source/s2/subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim'
    path_2 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/source/s2/subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.1.dim'
    path_3 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/source/s2/subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.2.dim'

    out_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/merged/s2/s2.dim'
    # out_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/convert/tif_gdal/'
    read_1 = FileProcessor('file_1', path_1) \
        .add_op(Read(module='snap'))
    read_2 = FileProcessor('file_1', path_2) \
        .add_op(Read(module='snap'))
    read_3 = FileProcessor('file_1', path_3) \
        .add_op(Read(module='snap'))

    merge_1 = LinkProcessor('merge_1', [read_1, read_2, read_3]) \
        .add_op(Stack(bands=[['B2', 'B3'], ['B3'], ['B3', 'B4']])) \
        .add_op(Write(path=out_path, module='snap'))

    ctx = Context()
    file_executor_1 = ProcessingExecutor(ctx)
    merge_1.set_executor(file_executor_1)
    w_gen_1 = merge_1.execute()
    for i, x in enumerate(w_gen_1):
        print(x)

def s1_grd():

    out_path_1 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/convert/s1_dim/grd_gdal.tif'
    s1_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/s1/S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE'

    s2_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/s2/S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE'
    ctx = Context()
    # gdal_obj = Raster(s1_path)
    read_op = Read(module='snap')
    result = read_op(s1_path, ctx, bname_word_included=True)
    ap_or = ApplyOrbit()
    ap_result = ap_or(result, ctx)
    calib = Calibrate()
    cal_result = calib(ap_result, ctx)
    tc = TerrainCorrection()
    tc_result = tc(cal_result, ctx)
    subset = Subset(bounds=[128.13, 35.8, 128.8, 35.6], epsg=4326)
    subset_result = subset(tc_result, ctx)
    wr_op = Write(path=out_path_1, module='gdal', out_ext='tif')
    wr_op(subset_result, ctx)
    print()
    # gdal tif to snap tif

def s1_slc():
    out_path_1 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/convert/s1_dim/s2_snap_speckle.tif'
    s2_path = '/home/airs_khw/mount/expand/data/etri/PSInSAR/new/tutorial/input/S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE'

    ctx = Context()
    read_op = Read(module='snap')
    result = read_op(s2_path, ctx, bname_word_included=True)
    ap_or = ApplyOrbit()
    ap_result = ap_or(result, ctx)
    calib = Calibrate()
    cal_result = calib(ap_result, ctx)
    tmr = ThermalNoiseRemoval()
    tmr_result = tmr(cal_result, ctx)
    deburst = TopsarDeburst()
    deburst_result = deburst(tmr_result, ctx)
    tc = TerrainCorrection()
    tc_result = tc(deburst_result, ctx)
    subset = Subset(bounds=[128.13, 35.8, 128.8, 35.6], epsg=4326)
    subset_result = subset(tc_result, ctx)
    speckle = SpeckleFilter()
    speckle_result = speckle(subset_result, ctx)
    wr_op = Write(path=out_path_1, module='snap', out_ext='tif')
    wr_op(speckle_result, ctx)
    print()

def s2():
    out_path_1 = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/convert/s2_dim/s2_snap.tif'
    s2_original_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/s2/S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE'
    s2_dim_path = '/home/airs_khw/mount/expand/data/etri/_sentinel_1_2/export/source/s2/subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim'

    ctx = Context()
    read_op = Read(module='snap', bands=['B2', 'B3', 'B4'])
    result = read_op(s2_original_path, ctx)
    denoise = NLMeanDenoising()
    denoise_result = denoise(result, ctx)
    print()


if __name__ == '__main__':
    # s1()
    # convert()

    # s1_grd()
    # s1_slc()
    # s2()
    # merge()
    # merge_tif()
    merge()