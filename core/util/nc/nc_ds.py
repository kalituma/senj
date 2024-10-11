from typing import List, AnyStr
from netCDF4 import Dataset, Dimension

from core.util.errors import ContainedBandError
from core.util.nc import get_band_names_nc, read_band

def copy_dimenstions(src_ds:Dataset, target_ds:Dataset):
    for name, dim in src_ds.dimensions.items():
        target_ds.createDimension(name, len(dim) if not dim.isunlimited() else None)
    return target_ds


def copy_nc_ds(src_ds:Dataset, selected_bands:List[AnyStr]=None):

    if selected_bands:
        matched_band = selected_bands
        for bname in matched_band:
            assert (bname in get_band_names_nc(src_ds)), f'Selected bands are not in the source product: {bname}'
    else:
        matched_band = get_band_names_nc(src_ds)

    if len(matched_band) == 0:
        raise ContainedBandError(list(matched_band))

    target_ds = Dataset('inmemory.nc', 'w', diskless=True, persist=False)
    copy_dimenstions(src_ds, target_ds)

    for name in matched_band:
        src_band = read_band(src_ds, name)
        x = target_ds.createVariable(name, src_band.datatype, src_band.dimensions)
        target_ds[name].setncatts(src_band.__dict__)
        target_ds[name][:] = src_band[:]


    target_ds.setncatts(src_ds.__dict__)
    src_ds.close()

    return target_ds

