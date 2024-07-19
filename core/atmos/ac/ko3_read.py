import os,sys
import numpy as np
from core import atmos

def ko3_read(ko3file=None):


    if ko3file is None:
        ko3file = atmos.config['data_dir']+'/Shared/k_o3_anderson.txt'

    ko3data=[]
    ko3wave=[]
    with open(ko3file, 'r') as f:
        for line in f:
            if line[0] == '!': continue
            if line[0] == '/': continue
            split = line.split(' ')
            if len(split) != 2: continue
            ko3data.append(float(split[1]))
            ko3wave.append(float(split[0])/1000.)
    ko3={"wave":np.asarray(ko3wave), "data":np.asarray(ko3data)}
    return(ko3)
