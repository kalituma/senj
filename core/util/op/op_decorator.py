from typing import Callable, TYPE_CHECKING, Type, Tuple, AnyStr
from functools import wraps
from pathlib import Path
from core.util.errors import ProductTypeError, OperationTypeError, ModuleError, ExtensionError

if TYPE_CHECKING:
    from core.raster import Raster, RasterType
    from core.operations.parent import Op

def check_init_operation(*init_ops:Tuple[AnyStr]):
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

def op_constraint(avail_module_types:list, must_after:Type["Op"]=None):
    def decorator(cls):
        setattr(cls, 'avail_types', avail_module_types)
        setattr(cls, 'must_after', must_after)
        return cls
    return decorator

def call_constraint(module_types=None, product_types=None, ext=None):
    def decorator(func:Callable):
        check_module_type = lambda x: True if x in module_types else False
        check_product_type = lambda x: True if x in product_types else False

        @wraps(func)
        def func_wrapper(self, raster:"Raster", *args, **kwargs):
            if module_types is not None:
                if not check_module_type(raster.module_type):
                    raise ModuleError(module=raster.module_type.value, available_modules=[t.value for t in module_types])
            if product_types is not None:
                if not check_product_type(raster.product_type):
                    raise ProductTypeError(supported_product=[t.value for t in product_types], current_product=raster.product_type.value)
            if ext is not None:
                raster_ext = Path(raster.path).suffix[1:].lower()
                if not raster_ext in ext:
                    raise ExtensionError(ext=raster_ext, available_exts=ext)
            return func(self, raster, *args, **kwargs)

        return func_wrapper
    return decorator