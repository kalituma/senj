import importlib

def import_lazy(module_name, package=None):
    return importlib.import_module(module_name, package)

def load_obj(obj_name:str, module_name:str, pkg_name:str):
    pkg = import_lazy(module_name=module_name, package=pkg_name)
    return getattr(pkg, obj_name)

def load_snap(obj_name:str, module_name='esa_snappy', pkg_name:str= 'esa_snappy'):
    return load_obj(obj_name=obj_name, module_name=module_name, pkg_name=pkg_name)

def load_gdal(module_name='osgeo.gdal', pkg_name:str= 'gdal'):
    return import_lazy(module_name=module_name, package=pkg_name)

def load_ogr(module_name='osgeo.ogr', pkg_name:str= 'ogr'):
    return import_lazy(module_name=module_name, package=pkg_name)

def load_osr(module_name='osgeo.osr', pkg_name:str= 'osr'):
    return import_lazy(module_name=module_name, package=pkg_name)
