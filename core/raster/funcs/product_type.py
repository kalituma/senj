from jsonpath_ng.ext import parse
from core.util import ProductType

def check_product_type(meta_dict: dict) -> ProductType:
    if meta_dict is None or len(meta_dict) == 0:
        return ProductType.UNKNOWN

    find_product = lambda x : [field.value for field in parse(x).find(meta_dict)]

    s1_mission = '$.Abstracted_Metadata.MISSION'
    s2_mission = '$.Level-1C_User_Product.General_Info.Product_Info.Datatake.SPACECRAFT_NAME'
    try:
        if len(find_product(s1_mission)) > 0:
            found_values = find_product(s1_mission)
            if 'sentinel-1' in found_values[0].lower():
                return ProductType.S1
            else:
                return ProductType.UNKNOWN

        elif len(find_product(s2_mission)) > 0:
            found_values = find_product(s2_mission)
            if 'sentinel-2' in found_values[0].lower():
                return ProductType.S2
            else:
                return ProductType.UNKNOWN
        else:
            return ProductType.UNKNOWN
    except:
        return ProductType.UNKNOWN


