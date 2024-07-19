import numpy as np
import os, bz2
from core import atmos


def f0_get(f0_file=None, f0_dataset='Thuillier2003'):


    if f0_file is None:
        for ext in ['txt', 'txt.bz2']:
            f0_file = os.path.join(atmos.PROJECT_PATH, 'data', 'atmos', 'Solar', f'{f0_dataset}.{ext}')
            if os.path.exists(f0_file):
                break

    f0data=[]
    f0wave=[]
    lines = []
    if os.path.exists(f0_file):
        p, e = os.path.splitext(f0_file)
        if e == '.txt':
            with open(f0_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        elif e == '.bz2':
            with bz2.open(f0_file, 'rb') as f:
                lines = [l.decode('utf-8') for l in f.readlines()]

        for line in lines:
                line = line.strip()
                if line[0] in ['#', '!', '/']: continue
                split = line.split(' ')
                if len(split) != 2: continue
                f0data.append(float(split[1]))
                f0wave.append(float(split[0]))
        f0={"wave":np.asarray(f0wave), "data":np.asarray(f0data)}
        return(f0)
    else:
        print(f'F0 reference {f0_dataset} not found in {atmos.PROJECT_PATH}/data/Solar/')
        return()