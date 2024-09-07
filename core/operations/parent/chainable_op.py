from typing import Union
from core.util.op import CHAIN_KEY, MODULE_TYPE
from core.operations.parent import Op

class ChainableOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)
        self._init_flag = False
        self._end_flag = False
        self._chain_key:CHAIN_KEY = CHAIN_KEY.NOTSET
        self.on('op_type_changed', self._update_chain_key)

    def _update_chain_key(self, module_type:MODULE_TYPE):
        if module_type == MODULE_TYPE.GDAL:
            self.chain_key = 'warp'

    @property
    def init_flag(self):
        return self._init_flag

    @init_flag.setter
    def init_flag(self, value:bool):
        self._init_flag = value

    @property
    def end_flag(self):
        return self._end_flag

    @end_flag.setter
    def end_flag(self, value:bool):
        self._end_flag = value

    @property
    def chain_key(self):
        return self._chain_key

    @chain_key.setter
    def chain_key(self, value:Union[CHAIN_KEY, str]):
        if isinstance(value, str):
            self._chain_key = CHAIN_KEY.from_str(value)
        elif isinstance(value, CHAIN_KEY):
            self._chain_key = value
        else:
            raise ValueError(f"Unknown CHAIN_KEY: {value}")
