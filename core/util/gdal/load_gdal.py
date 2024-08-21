import os
from pathlib import Path

from core.util import ProductType, assert_bnames, parse_meta_xml
from core.util.identify import planet_test
from core.util.gdal import read_tif, mosaic_tiles

def load_raster_gdal(path, product_type: ProductType, selected_bands: list[int] = None):
    in_path = path
    tile_mosaic = False

    ext = Path(in_path).suffix.lower()
    if ext == '.xml':
        tmp_meta = parse_meta_xml(in_path, product_type)
        base_path = Path(in_path).parent
        if product_type == ProductType.WV:
            tile_paths = [os.path.join(str(base_path), tile_info['FILENAME']) for tile_info in tmp_meta['TILE_INFO']]
            assert all([os.path.exists(tile_path) for tile_path in tile_paths]), f'All tile paths should be exist in {tile_paths}'
            ds = mosaic_tiles(tile_paths)
            tile_mosaic = True
        elif product_type == ProductType.PS:
            meta_path = in_path
            file_spec = planet_test(meta_path)
            assert 'analytic' in file_spec, 'analytic band is not found in the input file'
            ds = read_tif(file_spec['analytic']['path'])
        else:
            raise NotImplementedError(f'Product type({product_type}) is not implemented for the input process.')

    else:
        ds = read_tif(in_path)

    band_range = list(range(1, ds.RasterCount + 1))

    if selected_bands:
        assert_bnames(selected_bands, band_range, f'selected bands {selected_bands} is not found in {band_range}')

    return ds, selected_bands, tile_mosaic