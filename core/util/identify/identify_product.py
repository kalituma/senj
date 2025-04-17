from pathlib import Path

from core.util import ProductType, read_pickle
from core.util.identify import check_product_type_using_meta
from core.util.identify.indentifiers import ProductIdentifier

def identify_product(src_path_str:str) -> tuple[ProductType,str]:

    src_path = Path(src_path_str)
    if not src_path.exists():
        raise FileNotFoundError(f'{src_path_str} does not exist.')

    meta_path = ''
    ext = src_path.suffix

    if ext == '.tif':
        pkl = src_path.with_suffix('.pkl')
        if pkl.exists():
            meta_dict = read_pickle(pkl)
            return check_product_type_using_meta(meta_dict), str(pkl)

    for identifier_cls in ProductIdentifier.registry:
        if identifier_cls.can_identify(src_path_str):
            try:
                return identifier_cls.identify(src_path_str)
            except Exception as e:
                pass

    # todo: add warning message to alert that meta_path is not found
    return ProductType.UNKNOWN, meta_path