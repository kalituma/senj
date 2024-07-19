from typing import Callable, TYPE_CHECKING
from functools import wraps

if TYPE_CHECKING:
    from core.raster import Raster

def check_product_type(*allowed_types):
    def decorator(func:Callable):
        @wraps(func)
        def func_wrapper(self, raster:"Raster", *args, **kwargs):
            if raster.product_type in allowed_types:
                return func(self, raster, *args, **kwargs)
            else:
                raise ValueError(f'Product type should be {str(allowed_types)} for {self.__str__}, but got {raster.product_type.value}')
        return func_wrapper
    return decorator