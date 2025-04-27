from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path


from core.util import (
    get_btoi_from_tif, read_pickle, parse_meta_capella, parse_meta_xml, get_files_recursive
)
from core.util.snap import make_meta_dict_from_product, read_gpf
from core.util.nc import make_meta_dict_from_nc_ds
from core.util.gdal import make_meta_dict_from_grib
from core.raster import ProductType
from core.raster.funcs import update_meta_dict, process_provided_band_to_index, process_sentinel_planetscope_capella, process_worldview, process_goci_gk2a

if TYPE_CHECKING:
    from core.raster.funcs.reader import BaseRasterReader

class MetaBuilder(ABC):
    def __init__(self, reader: "BaseRasterReader"):
                
        self.reader = reader
        self.raster_path = self.reader.raster.path
        self.module_type = self.reader.module_type
        self.product_type = self.reader.product_type

        self.btoi_from_header: Optional[Dict[str, int]] = None
        
        self._meta_dict = None
    
    @property
    def meta_dict(self) -> Dict[str, Any]:
        return self._meta_dict
    
    @meta_dict.setter
    def meta_dict(self, value: Dict[str, Any]):
        self._meta_dict = value

    @abstractmethod
    def build_meta_dict(self, update_meta_bounds: bool) -> 'MetaBuilder':
        raise NotImplementedError('Subclasses must implement this method')

    def set_btoi_meta_dict(self):

        raw = self.reader.raster.raw

        if raw is None:
            return self

        if self.meta_dict is None:
            return self
        
        if self._contain_btoi_meta_dict():
            return self
        
        try:
            if self.btoi_from_header:
                b_to_i, i_to_b = process_provided_band_to_index(self.btoi_from_header)
                
            elif self.product_type in [ProductType.S1, ProductType.S2, ProductType.PS, ProductType.CP,
                                       ProductType.LDAPS, ProductType.CA, ProductType.K3]:
                b_to_i, i_to_b = process_sentinel_planetscope_capella(raw, self.module_type)
            
            elif self.product_type in [ProductType.WV]:
                b_to_i, i_to_b = process_worldview(self.meta_dict)
            
            elif self.product_type in [ProductType.GOCI_CDOM, ProductType.GOCI_AC, ProductType.GK2A]:
                b_to_i, i_to_b = process_goci_gk2a(raw, self.module_type)
            
            else:
                raise NotImplementedError(f'{self.product_type} is not implemented.')

            self.meta_dict['band_to_index'] = b_to_i
            self.meta_dict['index_to_band'] = i_to_b

        except Exception as e:
            print(f"Error initializing band name index: {e}")
    
        return self
    
    def after_build(self) -> Dict[str, Any]:
        self.set_btoi_meta_dict()
        if self.meta_dict:
            self.btoi_from_header = None
        return self.meta_dict
        
    def _contain_btoi_meta_dict(self) -> bool:
        return 'band_to_index' in self.meta_dict and 'index_to_band' in self.meta_dict
    
    def check_cached_meta(self) -> Optional[Dict[str, Any]]:
        
        ext = Path(self.raster_path).suffix
        pkl_meta_path = self.raster_path.replace(ext, '.pkl')
        
        if Path(pkl_meta_path).exists():
            return read_pickle(pkl_meta_path)
    
        return None

class TifMetaBuilder(MetaBuilder):
    def build_meta_dict(self, update_meta_bounds: bool=False) -> Dict[str, Any]:
        if Path(self.raster_path).suffix.lower() == '.tif':
            self.btoi_from_header = get_btoi_from_tif(self.raster_path)

        raw = self.reader.raster.raw
        meta_dict = self.check_cached_meta()

        if meta_dict is None:
            if self.product_type in [ProductType.CP]:
                meta_path = self.raster_path.replace('.tif', '.json')
                extended_meta_path = self.raster_path.replace('.tif', '_extended.json')
                assert Path(meta_path).exists() and Path(extended_meta_path).exists(), f'meta file not found in {meta_path} and {extended_meta_path}'
                meta_dict = parse_meta_capella(meta_path, extended_meta_path)
            elif self.product_type in [ProductType.WV, ProductType.PS, ProductType.CA, ProductType.K3]:
                tif_file_dim = [raw.RasterYSize, raw.RasterXSize]
                meta_dict = parse_meta_xml(self.raster_path, self.product_type, tif_file_dim)
                if update_meta_bounds and self.product_type == ProductType.WV:
                    meta_dict = update_meta_dict(meta_dict, raw, self.module_type)
            else:
                meta_dict = None            

        self.meta_dict = meta_dict

        return self.meta_dict

class SnapMetaBuilder(MetaBuilder):
    def build_meta_dict(self, update_meta_bounds: bool=False) -> Dict[str, Any]:
        assert self.product_type == ProductType.S1 or self.product_type == ProductType.S2, 'SNAP meta builder is only supported for S1 and S2 products'
        raw = self.reader.raster.raw
        
        if raw is None:
            raw = read_gpf(self.raster_path)
        self.meta_dict = make_meta_dict_from_product(raw, self.product_type)

        return self.meta_dict

class NcMetaBuilder(MetaBuilder):
    def build_meta_dict(self, update_meta_bounds: bool=False) -> Dict[str, Any]:
        assert self.product_type in [ProductType.GOCI_AC, ProductType.GOCI_CDOM, ProductType.SMAP, ProductType.GK2A], 'NC meta builder is only supported for GOCI_AC, GOCI_CDOM and GK2A products'
        raw = self.reader.raster.raw
        assert raw is not None, 'NC reader raw is None'
        self.meta_dict = make_meta_dict_from_nc_ds(raw)

        return self.meta_dict

class GribMetaBuilder(MetaBuilder):
    def build_meta_dict(self, update_meta_bounds: bool=False) -> Dict[str, Any]:
        assert self.product_type == ProductType.LDAPS, 'GRIB meta builder is only supported for LDAPS products'
        raw = self.reader.raster.raw
        self.meta_dict = make_meta_dict_from_grib(raw)
        return self.meta_dict
