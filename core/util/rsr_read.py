import fnmatch

def rsr_read(file=None):
    if file is not None:
        with open(file, 'r', encoding='utf-8') as f:
            rwave=[]
            rresp=[]
            bands=[]
            bid = 0
            data = dict()
            for i, line in enumerate(f.readlines()):
                if (line[0][:1] == '#') | (line[0][:1] == ';'):
                    if '/' in line: continue
                    if (fnmatch.fnmatch(line, '*Band*')) | (fnmatch.fnmatch(line, '*BAND*')):
                        tmp = line.split()
                        band = tmp[-1]
                        if bid > 0:
                            bdata = {'wave':rwave, 'response':rresp}
                            data[prev_band.lower()]=bdata
                            bands.append(prev_band.lower())
                        prev_band = band
                        bid+=1
                        rwave=[]
                        rresp=[]

                else:
                    ls = line.split()
                    if float(ls[0]) > 100:
                        rwave.append(float(ls[0])/1000.)
                    else:
                        rwave.append(float(ls[0]))
                    rresp.append(float(ls[1]))

            if len(rwave) != 0:
                bdata = {'wave':rwave, 'response':rresp}
                data[prev_band.lower()]=bdata
                bands.append(prev_band.lower())

        return data,bands