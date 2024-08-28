from core.operations.parent import Op

class ParamOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)
        self._snap_params = {}
    def add_param(self, **kwargs):
        self._snap_params.update(kwargs)

    def get_param(self, key:str):
        return self.snap_params.get(key, None)

    def del_param(self, key:str):
        del self.snap_params[key]

    @property
    def snap_params(self) -> dict:
        return self._snap_params

    @snap_params.setter
    def snap_params(self, snap_params:dict):
        self._snap_params = snap_params