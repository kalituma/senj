from core.util import ModuleType
from core.raster.funcs.meta import MetaBandsManager
from core.raster import Raster
from core.raster.funcs.reader import BaseRasterReader
from core.raster.funcs.adapter import NcRasterAdapter
from core.raster.funcs.meta import NcMetaBuilder

class NcReader(BaseRasterReader, NcRasterAdapter):    

    def _init_reader(self, file_path: str) -> None:

        self.initialize(file_path, ModuleType.NETCDF)
        self.set_meta_builder(NcMetaBuilder)

    def read(self, file_path: str, *args, **kwargs) -> Raster:

        self._init_reader(file_path)

        self.img_paths = self.load_img_paths()
        self.raster.raw = self.read_data(self.img_paths)

        self.meta_builder.build_meta_dict(False)
        self.raster.meta_dict = self.meta_builder.after_build()

        MetaBandsManager(self.raster).update_band_mapping(self.meta_builder.btoi_from_header)

        return self.raster