## def bundle_test
## lists files in given directory and returns dict with band and file path
## written by Quinten Vanhellemont, RBINS
## 2018-03-12
## modifications: 2018-03-14 (QV) added option to give .tif or metadata.xml files
##                2018-03-14 (QV) improved filtering to include clipped files
##                2018-03-19 (QV) added MS files in filtering
##                2021-02-24 (QV) new version for acg
##                2022-01-11 (QV) added AnalyticMS_8b
##                2022-02-21 (QV) added Skysat, include support for unzipped API downloads
##                2022-10-26 (QV) added scene_id to datafiles
##                2023-04-17 (QV) fix for Skysat scene_ids and selecting one from multiple files
##                2023-04-18 (QV) added PSScene and files/PSScene dname options
##                                added support for NTF files
##                2023-05-08 (QV) added support for composite files
##                2023-05-25 (QV) set sid to None if manifest is given
##                2024-08-00 modified by kalituma
import os
from pathlib import Path

def planet_test(tif_or_xml_path):

    ps_path = Path(tif_or_xml_path)
    if ps_path.is_dir():
        raise ValueError('The input path is a directory. Please provide a file path.')

    ps_dir = ps_path.parent
    in_stem = ps_path.stem
    in_ext = ps_path.suffix

    search_id = "_".join(in_stem.split("_")[:4])
    search_pattern = f'{search_id}*'

    ## include files/analytic_udm2 directory contents
    files = list(ps_dir.glob(search_pattern))
    files.sort()

    datafiles = {}
    for i, file in enumerate(files):
        stem = file.stem
        ext = file.suffix
        file_name = file.name

        if ext not in ['.json', '.tif', '.xml', '.ntf']:
            continue
        if '.aux.xml' in stem:
            continue ## skip QGIS files

        band,clp= None, ''

        if 'clip' in stem:
            clp = '_clip'

        if (f'Analytic_metadata{clp}.xml' in file_name) or (f'AnalyticMS_metadata{clp}.xml' in file_name) or \
                (f'AnalyticMS_8b_metadata{clp}.xml' in file_name):
            band = 'metadata'
        if 'metadata.json' in file_name:
            band = 'metadata_json'
        if ('Analytic{}.tif'.format(clp) in file_name) or ('AnalyticMS{}.tif'.format(clp) in file_name) or \
           ('AnalyticMS_8b{}.tif'.format(clp) in file_name) or ('analytic{}.tif'.format(clp) in file_name):
            band = 'analytic'
        if ('Analytic{}_file_format.ntf'.format(clp) in file_name) or ('AnalyticMS{}_file_format.ntf'.format(clp) in file_name)|\
           ('AnalyticMS_8b{}_file_format.ntf'.format(clp) in file_name) or ('analytic{}_file_format.ntf'.format(clp) in file_name):
            band = 'analytic_ntf'
        if ('DN_udm{}.tif'.format(clp) in file_name):
            band = 'udm'
        if ('udm2{}.tif'.format(clp) in file_name):
            band = 'udm2'
        if ('analytic_dn{}.tif'.format(clp) in file_name):
            band = 'analytic_dn'
        if ('panchromatic_dn{}.tif'.format(clp) in file_name):
            band = 'pan_dn'
        if ('pansharpened{}.tif'.format(clp) in file_name):
            band = 'pansharpened'
        if ('Analytic_SR{}.tif'.format(clp) in file_name) or ('AnalyticMS_SR_8b{}.tif'.format(clp) in file_name):
            band = 'sr'

        if ('composite.tif' in file_name):
            band = 'composite'
        if ('composite_udm2.tif' in file_name):
            band = 'composite_udm2'

        if band is None:
            continue
        if file.is_file():
            datafiles[band] = {"path":str(file), "file_name":file_name, "ext": ext}

    return datafiles
