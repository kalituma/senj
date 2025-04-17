from lxml import etree
from core.util.meta import etree_to_dict, read_xml_dict_from_path
def parse_cas500(meta_path: str) -> dict:

    return read_xml_dict_from_path(meta_path)