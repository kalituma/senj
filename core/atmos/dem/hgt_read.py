import os
import struct
import numpy as np

def hgt_read(file):

    if '.gz' in file:
        import gzip
        with gzip.open(file,'rb') as f:
            data_read = f.read()
    elif '.zip' in file:
        import zipfile
        zfile = '{}.{}'.format(os.path.basename(file).split('.')[0], 'hgt')
        with zipfile.ZipFile(file, mode='r') as f:
            data_read = f.read(zfile)
    else:
        with open(file,'rb') as f:
            data_read = f.read()

    bn = os.path.basename(file)
    if 'SRTMGL3' in bn: # len data_read = 2884802
        dim = (1201,1201)
    elif 'SRTMGL1' in bn: # len data_read = 25934402
        dim = (3601,3601)

    ## big endian, unsigned shorts
    data = struct.unpack('>{}'.format('H'*dim[0]*dim[1]),data_read)
    data = np.asarray(data).reshape(dim)

    data[data > 32768] -= 65535
    return(data)
