from core.raster.gpf_module import create_product_data

def copy_to_raw_gpf(product, band_name, band_arr):

    t_band = product.getBand(band_name)
    band_raster = create_product_data(band_arr)
    t_band.setRasterData(band_raster)