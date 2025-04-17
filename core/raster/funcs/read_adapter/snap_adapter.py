from typing import List, TYPE_CHECKING

from core.util.snap import load_raster_gpf, mosaic_gpf
from core.raster.funcs.read_adapter import BaseAdapter

if TYPE_CHECKING:
    from esa_snappy import Product
    
class SnapAdapter(BaseAdapter):    
    def load_raster(self, img_paths:List[str], *args, **kwargs) -> "Product":
        datasets = load_raster_gpf(img_paths)

        if len(datasets) == 1:
            return datasets[0]
        else:
            self.update_meta_bounds = True
            return mosaic_gpf(datasets)
