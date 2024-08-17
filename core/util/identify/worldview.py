import os, glob
from pathlib import Path

def worldview_test(bundle_in):

    datafiles = {}

    wv_path = Path(bundle_in)
    if wv_path.is_dir():
        raise ValueError('Worldview bundle should be a file, not a directory')
    else:
        wv_dir_path = wv_path.parent
        stem = wv_path.stem
        metafiles = list(wv_dir_path.glob(f'{stem.split("_")[0]}*.XML'))

    metafiles.sort()
    if len(metafiles) > 0:
        for idx, mf in enumerate(metafiles):
            mf_str = str(mf)
            if ('.aux.' not in mf_str) and ('README' not in mf_str) and ('(1)' not in mf_str):
                datafiles['metadata'] = {'path': mf, 'fname': mf.name}

    return datafiles

