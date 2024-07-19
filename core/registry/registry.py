class Registry:
    def __init__(self, name:str):
        self._reg_name = name
        self._reg_dict = {}

    def __len__(self):
        return len(self._reg_dict)

    def __contains__(self, name):
        return self.get(name) is not None

    @property
    def reg_name(self):
        return self._reg_name

    @property
    def reg_dict(self):
        return self._reg_dict

    def get(self, reg_name:str):
        reg_func = None

        if not isinstance(reg_name, str):
            raise ValueError('registered name must be a string')

        if reg_name in self._reg_dict:
            reg_func = self._reg_dict[reg_name]

        return reg_func

    def _reg(self, reg_name=None, reg_func=None, **kwargs):

        if isinstance(reg_name, str):
            reg_name = [reg_name]

        for name in reg_name:
            if name in self._reg_dict:
                existed_func = self._reg_dict[name]
                raise ValueError(f'{name} is already registered')
            self._reg_dict[name] = reg_func

    def reg(self, name, reg_func=None, **kwargs):

        if reg_func is not None:
            self._reg(name, reg_func)
            return reg_func

        def _reg_func(reg_func):
            self._reg(name, reg_func, **kwargs)
            return reg_func

        return _reg_func
