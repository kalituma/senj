import importlib
import pkgutil

def _import_submodule(package:str):
    pkg = importlib.import_module(package)
    for _, name, is_pkg in pkgutil.walk_packages(pkg.__path__):
        full_name = f'{package}.{name}'
        importlib.import_module(full_name)
        if is_pkg:
            _import_submodule(full_name)

class Registry:
    def __init__(self, name:str, package:str):
        self._package = package
        self._reg_name = name
        self._reg_dict = {}

    def __len__(self):
        return len(self._reg_dict)

    def __contains__(self, name):
        return self[name] is not None

    @property
    def reg_name(self):
        return self._reg_name

    @property
    def reg_dict(self):
        return self._reg_dict

    def __getitem__(self, name:str):
        try:
            return self.reg_dict[name]
        except KeyError:
            try:
                _import_submodule(self._package)
                return self.reg_dict[name]
            except ImportError:
                raise KeyError(name)

    def _reg(self, reg_name:str=None, reg_obj=None, **kwargs):

        if reg_name in self._reg_dict:
            raise ValueError(f'{reg_name} is already registered')
        self._reg_dict[reg_name] = reg_obj

    def reg(self, name, reg_func=None, **kwargs):

        if reg_func is not None:
            self._reg(name, reg_func)
            return reg_func

        def _reg_func(reg_func):
            self._reg(name, reg_func, **kwargs)
            return reg_func

        return _reg_func
