from pathlib import Path
from lxml import etree

from core.util import ProductType

def rgb_test(tif_path, satellite_name):
    datafiles = {}

    capella_path = Path(tif_path)
    if capella_path.is_dir():
        raise ValueError('Capella bundle should be a file, not a directory')
    else:
        capella_dir_path = capella_path.parent
        stem = capella_path.stem
        metafiles = list(capella_dir_path.glob(f'{"_".join(stem.split("_")[:-2])}*.xml'))

    metafiles.sort()

    for mf in metafiles:
        mf_str = str(mf)
        root = etree.parse(mf_str)
        mission_attrs = root.xpath('//General/Satellite/text()')
        if len(mission_attrs) > 0:
            if satellite_name in mission_attrs[0]:
                datafiles['metadata'] = {'path': mf_str}

    assert 'metadata' in datafiles, f'No meta data file found in {capella_dir_path}'

    return datafiles
def cas500_test(tif_path):
    return rgb_test(tif_path, 'CAS500')

def k3_test(tif_path):
    return rgb_test(tif_path, 'KOMPSAT-3')