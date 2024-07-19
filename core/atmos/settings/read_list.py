def read_list(file):
    data_list = []
    with open(file, 'r', encoding='utf-8') as f:
        for il, line in enumerate(f.readlines()):
            line = line.strip()
            if len(line) == 0: continue # skip empty lines
            if line[0] in ['#', ';']: continue
            data_list.append(line)
    return(data_list)
