from typing import Callable, TYPE_CHECKING
from functools import wraps

from core.util import ProductTypeError, OperationTypeError

if TYPE_CHECKING:
    from core.raster import Raster
    from core.operations import Op

def check_operation(*init_ops:tuple[str]):
    def decorator(func:Callable):
        @wraps(func)
        def func_wrapper(self, op:"Op", *args, **kwargs):
            if len(self.ops) == 0:
                if op.op_name in init_ops:
                    return func(self, op, *args, **kwargs)
                else:
                    raise OperationTypeError(supported_ops=list(init_ops), current_op=op.op_name)
            else:
                return func(self, op, *args, **kwargs)
        return func_wrapper
    return decorator

def check_product_type(*allowed_types):
    def decorator(func:Callable):
        @wraps(func)
        def func_wrapper(self, raster:"Raster", *args, **kwargs):
            if raster.product_type in allowed_types:
                return func(self, raster, *args, **kwargs)
            else:
                raise ProductTypeError(supported_product=[t.value for t in allowed_types], current_product=raster.product_type.value)
        return func_wrapper
    return decorator