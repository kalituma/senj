import json
import pickle

def write_json(data, path,):
    with open(path, 'w') as f:
        json.dump(data, f)

def write_pickle(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)

def read_pickle(path):
    with open(path, 'rb') as f:
        return pickle.load(f)