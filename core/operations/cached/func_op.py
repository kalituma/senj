import uuid
from typing import TYPE_CHECKING

from core.operations.parent.op import Op
from core import OPERATIONS, LAMBDA

from core.util.op import OP_Module_Type, op_constraint, FUNC_OP
from core.raster import Raster
from core.vector import Vector

if TYPE_CHECKING:
    from core.base import GeoData
    from core.logic.context import Context
    

@OPERATIONS.reg(name=FUNC_OP)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL])
class FuncOp(Op):
    def __init__(self, func_name:str, **kwargs):
        super().__init__(FUNC_OP)
        self.func_name = func_name
        self.kwargs = kwargs

    def __call__(self, data: "GeoData", context: "Context", *args, **kwargs):
        func = LAMBDA.__get_attr__(name=self.func_name, attr_name='constructor')
        
        temp_path = f"/vsimem/memory_output_{uuid.uuid4()}"
        out_ds = func(data.raw, temp_path, **self.kwargs)
        
        if hasattr(out_ds, 'RasterCount'):
            new_raster = Raster.from_raster(data)
            new_raster.raw = out_ds
            return new_raster
        else:
            new_vector = Vector.like(data)
            new_vector.raw = out_ds
            return new_vector
