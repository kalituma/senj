from typing import List, TYPE_CHECKING
from pathlib import Path
from core.util.snap import load_raster_gpf, mosaic_gpf, write_gpf
from core.raster.funcs.adapter import BaseRasterAdapter

if TYPE_CHECKING:
    from esa_snappy import Product
    
ALLOWED_EXTENSIONS = ['.dim', '.tif']

class SnapRasterAdapter(BaseRasterAdapter):
    def read_data(self, img_paths:List[str], *args, **kwargs) -> "Product":
        datasets = load_raster_gpf(img_paths)

        if len(datasets) == 1:
            return datasets[0]
        else:
            self.update_meta_bounds = True
            return mosaic_gpf(datasets)
        
    def write_data(self, ds: "Product", out_path:str, format_type:str= 'BEAM-DIMAP', *args, **kwargs):
        
        assert Path(out_path).suffix.lower() in ALLOWED_EXTENSIONS
        write_gpf(ds, out_path, format_type)