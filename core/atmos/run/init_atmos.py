from typing import TYPE_CHECKING

from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse


from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run import build_l1r

if TYPE_CHECKING:
    from esa_snappy import Product

def init_atmos(product:"Product", atmos_conf_path, selected_bands=None):

    if not selected_bands:
        selected_bands = list(product.getBandNames())

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])

    # read_det(product, selected_bands)
    build_l1r(product)



