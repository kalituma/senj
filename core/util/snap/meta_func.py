import numpy as np
from core.util import load_snap

def grid_geom(elem):

    values = []
    for sub in elem.getAttributes():
        value_str = sub.getData().getElemString()
        values.append([float(i) for i in value_str.split(' ')])
    return np.array(values)

def get_metadata_recursive(element, path):
    if '/' in path:
        child_name, remaining_path = path.split('/', 1)
        child_element = element.getElement(child_name)
        if child_element is not None:
            return get_metadata_recursive(child_element, remaining_path)
    else:
        child_name = path
        child_element = element.getElement(child_name)
        return child_element
    return None

def get_metadata_value(element, path):
    if '/' in path:
        child_name, remaining_path = path.split('/', 1)
        child_element = element.getElement(child_name)
        if child_element is not None:
            return get_metadata_value(child_element, remaining_path)
    else:
        attribute = element.getAttribute(path)
        if attribute is not None:
            return attribute.getData().getElemString()
    return None

def set_meta_recursive(element, meta_dict):

    jpy = load_snap('jpy')

    metadata_element = jpy.get_type('org.esa.snap.core.datamodel.MetadataElement')

    for key, value in meta_dict.items():
        if isinstance(value, dict):
            sub_element = set_meta_recursive(metadata_element(key), value)
            element.addElement(sub_element)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sub_element = set_meta_recursive(metadata_element(key), item)
                    element.addElement(sub_element)
                else:
                    element.setAttributeString(key, item)
        else:
            try:
                element.setAttributeString(key, value)
            except Exception as e:
                print(e)


    return element

def build_meta_dict(element, meta_dict=None):

    if meta_dict is None:
        meta_dict = {}

    prev_sub_name = ''
    for sub in element.getElements():
        elem_dict = None
        if sub.getNumElements() > 0:
            curr_name = sub.getName()
            if curr_name == prev_sub_name:
                if isinstance(meta_dict[prev_sub_name],dict):
                    elem_arr = []
                    elem_arr.append(meta_dict[prev_sub_name])
                    meta_dict[prev_sub_name] = elem_arr
                elem_dict = build_meta_dict(sub, None)
                meta_dict[curr_name].append(elem_dict)
            else:
                elem_dict = build_meta_dict(sub, None)
                meta_dict[sub.getName()] = elem_dict

            prev_sub_name = sub.getName()

        if sub.getNumAttributes() > 0:
            prev_att_name = ''
            att_dict = {}
            for sub_att in sub.getAttributes():
                # data_type_str = ProductData.getTypeString(sub_att.getDataType())
                product_data = sub_att.getData()
                curr_name = sub_att.getName()
                if curr_name == prev_att_name:
                    if isinstance(att_dict[prev_att_name],str):
                        elem_arr = []
                        elem_arr.append(att_dict[prev_att_name])
                        att_dict[prev_att_name] = elem_arr
                    att_dict[curr_name].append(product_data.getElemString())
                else:
                    att_dict[curr_name] = product_data.getElemString()
                prev_att_name = sub_att.getName()

            if sub.getName() in meta_dict:
                if not elem_dict:
                    if isinstance(meta_dict[sub.getName()], dict):
                        meta_dict[sub.getName()] = [meta_dict[sub.getName()]]
                        meta_dict[sub.getName()].append(att_dict.copy())
                    elif isinstance(meta_dict[sub.getName()], list):
                        meta_dict[sub.getName()].append(att_dict.copy())
                else:
                    elem_dict.update(att_dict)
            else:
                meta_dict[sub.getName()] = att_dict.copy()

    return meta_dict