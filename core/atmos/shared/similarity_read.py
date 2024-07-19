import numpy as np
from core import atmos

def similarity_read(file=None):


    if file is None:
        file = '{}/Shared/REMSEM/similarityspectrumtable.txt'.format(atmos.config['data_dir'])

    ss_data = {'wave':np.ndarray(0), 'ave':np.ndarray(0), 'std':np.ndarray(0), 'cv':np.ndarray(0)}

    with open(file, 'r') as f:
        for i,line in enumerate(f.readlines()):
            line = line.strip()
            sp = line.split()
            if i == 0:
                continue
            else:
                j = 0
                while j<len(sp):
                    ss_data['wave']=np.append(ss_data['wave'],float(sp[j])/1000.)
                    ss_data['ave']=np.append(ss_data['ave'],float(sp[j+1]))
                    ss_data['std']=np.append(ss_data['std'],float(sp[j+2]))
                    ss_data['cv']=np.append(ss_data['cv'],float(sp[j+3]))
                    j+=4

    ## sort indices
    idx = np.argsort(ss_data['wave'])
    for k in ss_data.keys(): ss_data[k]=ss_data[k][idx]
    return(ss_data)
