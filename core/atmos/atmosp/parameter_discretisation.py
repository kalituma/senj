import numpy as np
from core import atmos

def parameter_discretisation():

    param = {}
    header = None
    with open(atmos.config['parameter_discretisation'], 'r', encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0: continue
            if line[0] in ['#',';']: continue
            split = line.split('=')
            if split[0] == 'header':
                header = split[1].split(',')
            else:
                if header is None: continue
                tmp = [i.strip() for i in line.split(',')]
                par = tmp[0]
                val = {h:tmp[i] for i,h in enumerate(header)}
                for i in val:
                    if val[i] in ['False', 'false']: val[i] = False
                    if val[i] in ['True', 'true']: val[i] = True
                    if val[i] in ['None', 'none']: val[i] = None
                    ## convert to the requested type
                    if i in ['scale_factor', 'add_offset']:
                        try:
                            val[i] = np.array(val[i]).astype(val['source_type']).ravel()[0]
                        except:
                            val[i] = np.nan
                param[par]=val

    return(param)
