import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING, List, List, AnyStr, Union

from core import OPERATIONS
from core.operations import CachedOp, Context
from core.operations import ATMOSCORR_OP
from core.util.op import op_constraint, call_constraint, OP_TYPE
from core.util import ProductType, is_contained, glob_match
from core.raster.funcs import get_band_name_and_index, get_band_grid_size
from core.raster.funcs import apply_atmos, write_l2r_as_map

if TYPE_CHECKING:
    from core.raster import Raster

@OPERATIONS.reg(name=ATMOSCORR_OP, conf_no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.SNAP, OP_TYPE.GDAL])
class AtmosCorr(CachedOp):
    def __init__(self, bands:List[Union[AnyStr, int]], band_slots:List[AnyStr], write_map:bool=False, map_dir:str=None, map_stem:str=None,
                 det_bnames:List[AnyStr]=None, det_bword_included=False, det_bpattern=None):
        super().__init__(ATMOSCORR_OP)
        self.target_band_names:List[Union[AnyStr,int]] = bands
        self.target_band_slot:List[AnyStr] = band_slots
        self.det_names:List[AnyStr] = det_bnames
        self.det_bpattern = det_bpattern
        self.det_bword_included = det_bword_included
        self.write_map = write_map
        self.map_dir = map_dir
        self.map_stem = map_stem

        if self.write_map:
            assert self.map_dir, 'map_dir should be provided when write_map is True'
            if not self.map_stem:
                self.map_stem = 'l2r_map'

        assert len(self.target_band_names) == len(self.target_band_slot), 'target_band_names and target_band_slot should have the same length'

    @call_constraint(product_types=[ProductType.S2, ProductType.WV, ProductType.PS])
    def __call__(self, raster:"Raster", context:Context, *args, **kwargs):

        self.target_band_names, target_band_indices = get_band_name_and_index(raster, band_id_list=self.target_band_names)
        raster = self.load_bands(raster, self.target_band_names, self.target_band_slot, context)

        det_dict = det_names = None
        if self.det_names:
            self.det_bword_included = False

        if self.det_bword_included:
            assert self.det_bpattern, 'det_bword should be provided when det_bword_included is True'
            # find the band with glob pattern with asterisk described in det_bands
            all_bands = raster.get_band_names()
            self.det_names = glob_match(all_bands, self.det_bpattern)

            if len(self.det_names) == 0:
                raise ValueError(f'No matching det band found in target raster: {self.det_bpattern}')

        if self.det_names:
            self.det_names, det_band_indices = get_band_name_and_index(raster, band_id_list=self.det_names)
            raster, det_dict, det_names = self.load_det(raster, self.det_names, context)

        if raster.product_type == ProductType.S2:
            assert det_names, 'Sentinel-2 product should have detector bands.'

        l2r, global_attrs = apply_atmos(raster, raster.product_type, self.target_band_names, det_dict=det_dict, det_names=det_names)

        if self.write_map:
            Path(self.map_dir).mkdir(parents=True, exist_ok=True)

            if not self.map_stem:
                if Path(raster.path).stem != '':
                    self.map_stem = f'{Path(raster.path).stem}_l2r_map'
                else:
                    self.map_stem = 'l2r_map'

            write_l2r_as_map(l2r, global_attrs, out_dir=self.map_dir, out_file_stem=self.map_stem)

        bands = {}
        for key, value in l2r['bands'].items():
            bands[value['att']['band_name']] = {}
            value['data'][np.isnan(value['data'])] = -9999
            bands[value['att']['band_name']]['value'] = value['data']
            bands[value['att']['band_name']]['slot'] = key
            bands[value['att']['band_name']]['no_data'] = -9999

        raster.bands = bands
        raster = self.post_process(raster, context)

        return raster

    def load_bands(self, raster:"Raster", target_band_names:List[AnyStr], target_band_slot:List[AnyStr], context) -> "Raster":
        raster = self.pre_process(raster, context, bands_to_load=target_band_names)
        for bname, bslot in zip(target_band_names, target_band_slot):
            raster[bname]['slot'] = bslot
        return raster

    def load_det(self, raster:"Raster", det_names:List[AnyStr], context) -> tuple["Raster", dict, list[str]]:

        size_per_band = get_band_grid_size(raster)

        res_set = set()
        for bname in self.target_band_names:
            x_res = int(size_per_band[bname]['x_res'])
            if x_res not in res_set:
                res_set.add(x_res)

        det_res_map = {}

        try:
            for det_bname in det_names:
                det_res = int(size_per_band[det_bname]['x_res'])
                if det_res in res_set and det_res not in det_res_map:
                    det_res_map[f'{det_res}'] = det_bname
        except KeyError:
            raise ValueError(f'No matching band found in target raster: {det_bname}')

        assert len(det_res_map) == len(res_set), f'Detectors should have the same resolution case number with bands. (det:{len(det_res_map)},bands:{len(res_set)})'

        # target_bands = target_bands + [target_det]
        det_names = list(det_res_map.values())
        raster = self.pre_process(raster, context, bands_to_load=det_names)

        for det_res, det_bname in det_res_map.items():
            det_elems = np.unique(raster[det_bname]['value']).tolist()
            assert is_contained(det_elems, src_list=[2, 3, 4, 5, 6, 7]), 'Detector band should have values from 2 to 7.'

        det_dict = {res: raster[det_bname]['value'] for res, det_bname in det_res_map.items()}

        for det_bname in det_names:
            del raster.bands[det_bname]

        return raster, det_dict, det_names