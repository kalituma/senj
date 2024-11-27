import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING, List, List, AnyStr, Union

from core import OPERATIONS
from core.logic import Context
from core.operations.parent import CachedOp, SelectOp
from core.util.op import op_constraint, call_constraint, OP_Module_Type, ATMOSCORR_OP
from core.util import ProductType, is_contained, glob_match, expand_var
from core.raster.funcs import get_band_name_and_index, get_band_grid_size
from core.raster.funcs import apply_atmos, write_l2r_as_map

if TYPE_CHECKING:
    from core.raster import Raster

@OPERATIONS.reg(name=ATMOSCORR_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP, OP_Module_Type.GDAL])
class AtmosCorr(CachedOp, SelectOp):
    def __init__(self, bands:List[Union[AnyStr, int]], band_slots:List[AnyStr], write_map:bool=False, map_dir:str=None, map_stem:str=None,
                 det_bnames:List[AnyStr]=None, det_bword_included=False, det_bpattern=None):
        super().__init__(ATMOSCORR_OP)
        self._target_band_names:List[Union[AnyStr,int]] = bands
        self._target_band_slot:List[AnyStr] = band_slots
        self._det_names:List[AnyStr] = det_bnames
        self._det_bpattern = det_bpattern
        self._det_bword_included = det_bword_included
        self._write_map = write_map
        self._map_dir = expand_var(map_dir)
        self._map_stem = map_stem

        if self._write_map:
            assert self._map_dir, 'map_dir should be provided when write_map is True'
            if not self._map_stem:
                self._map_stem = 'l2r_map'

        assert len(self._target_band_names) == len(self._target_band_slot), 'target_band_names and target_band_slot should have the same length'

    @call_constraint(product_types=[ProductType.S2, ProductType.WV, ProductType.PS])
    def __call__(self, raster:"Raster", context:Context, *args, **kwargs):

        self._target_band_names, target_band_indices = get_band_name_and_index(raster, band_id_list=self._target_band_names)
        raster = self.load_bands(raster, self._target_band_names, self._target_band_slot, context)

        det_dict = det_names = None
        if self._det_names:
            self._det_bword_included = False

        if self._det_bword_included:
            assert self._det_bpattern, 'det_bword should be provided when det_bword_included is True'
            # find the band with glob pattern with asterisk described in det_bands
            all_bands = raster.get_band_names()
            self._det_names = glob_match(all_bands, self._det_bpattern)

            if len(self._det_names) == 0:
                raise ValueError(f'No matching det band found in target raster: {self._det_bpattern}')

        if self._det_names:
            self._det_names, det_band_indices = get_band_name_and_index(raster, band_id_list=self._det_names)
            raster, det_dict, det_names = self.load_det(raster, self._det_names, context)

        if raster.product_type == ProductType.S2:
            assert det_names, 'Sentinel-2 product should have detector bands.'

        l2r, global_attrs = apply_atmos(raster, raster.product_type, self._target_band_names, det_dict=det_dict, det_names=det_names)

        if self._write_map:
            Path(self._map_dir).mkdir(parents=True, exist_ok=True)

            if not self._map_stem:
                if Path(raster.path).stem != '':
                    self._map_stem = f'{Path(raster.path).stem}_l2r_map'
                else:
                    self._map_stem = 'l2r_map'

            write_l2r_as_map(l2r, global_attrs, out_dir=self._map_dir, out_file_stem=self._map_stem)

        bands = {}
        for key, value in l2r['bands'].items():
            bands[value['att']['band_name']] = {}
            value['data'][np.isnan(value['data'])] = -9999
            bands[value['att']['band_name']]['value'] = value['data']
            bands[value['att']['band_name']]['slot'] = key
            bands[value['att']['band_name']]['no_data'] = -9999

        raster.bands = bands
        raster = self.post_process(raster, context, clear=True)
        raster = SelectOp.pre_process(self, raster, selected_bands_or_indices=self._target_band_names, band_select=True)

        return raster

    def load_bands(self, raster:"Raster", target_band_names:List[AnyStr], target_band_slot:List[AnyStr], context) -> "Raster":
        raster = CachedOp.pre_process(self, raster, context, bands_to_load=target_band_names)
        for bname, bslot in zip(target_band_names, target_band_slot):
            raster[bname]['slot'] = bslot
        return raster

    def load_det(self, raster:"Raster", det_names:List[AnyStr], context) -> tuple["Raster", dict, list[str]]:

        size_per_band = get_band_grid_size(raster)

        res_set = set()
        for bname in self._target_band_names:
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
        raster = CachedOp.pre_process(self, raster, context, bands_to_load=det_names)

        # todo: should be improved to be faster
        # for det_res, det_bname in det_res_map.items():
        #     det_elems = np.unique(raster[det_bname]['value']).tolist()
        #     assert is_contained(det_elems, src_list=[1, 2, 3, 4, 5, 6, 7]), 'Detector band should have values from 1 to 7.'

        det_dict = {res: raster[det_bname]['value'] for res, det_bname in det_res_map.items()}

        for det_bname in det_names:
            del raster.bands[det_bname]

        return raster, det_dict, det_names