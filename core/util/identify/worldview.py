import os, glob
from pathlib import Path

def worldview_test(tif_or_xml_path:str):

    datafiles = {}

    wv_path = Path(tif_or_xml_path)
    if wv_path.is_dir():
        raise ValueError('Worldview bundle should be a file, not a directory')
    else:
        wv_dir_path = wv_path.parent
        stem = wv_path.stem
        metafiles = list(wv_dir_path.glob(f'{stem.split("_")[0]}*.XML'))

    metafiles.sort()

    for idx, mf in enumerate(metafiles):
        mf_str = str(mf)
        if ('.aux.' not in mf_str) and ('README' not in mf_str) and ('(1)' not in mf_str):
            datafiles['metadata'] = {'path': mf, 'fname': mf.name}

    assert 'metadata' in datafiles, f'No meta data file found in {wv_dir_path}'

    return datafiles

