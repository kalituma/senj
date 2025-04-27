from core.util import load_snap

def write_gpf(product, path, type='BEAM-DIMAP'):
    ProductIO = load_snap('ProductIO')
    ProductIO.writeProduct(product, path, type)
