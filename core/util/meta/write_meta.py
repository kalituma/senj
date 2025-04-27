from pathlib import Path
from core.util import write_pickle

def write_metadata(meta_dict:dict, path:str):

    out_dir = Path(path).parent
    out_stem = Path(path).stem
    pkl_path = str(out_dir / f"{out_stem}.pkl")
    write_pickle(meta_dict, pkl_path)