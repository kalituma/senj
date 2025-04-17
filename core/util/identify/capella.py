from pathlib import Path

def capella_test(tif_path):

    datafiles = {}
    
    capella_path = Path(tif_path)
    if capella_path.is_dir():
        raise ValueError('Capella bundle should be a file, not a directory')
    else:
        capella_dir_path = capella_path.parent
        stem = capella_path.stem
        metafiles = list(capella_dir_path.glob(f'{stem.split("_")[0]}*.json'))

    metafiles.sort()

    for mf in metafiles:
        mf_str = str(mf)
        if 'extended' in mf_str:
            datafiles['extended_metadata'] = {'path': mf, 'fname': mf.name}
        else:
            datafiles['metadata'] = {'path': mf, 'fname': mf.name}

    assert 'metadata' in datafiles, f'No meta data file found in {capella_dir_path}'
    assert 'extended_metadata' in datafiles, f'No extended meta data file found in {capella_dir_path}'

    return datafiles