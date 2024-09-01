import re
from typing import Dict

def validate_processor_relation(n_config:Dict, proc_list) -> bool:

    config_str = str(n_config)
    proc_refs = set(re.findall(r'{{(.*?)}}', config_str))
    assert all([proc_ref in proc_list for proc_ref in proc_refs]), f'Processor reference {proc_refs} not found in processor list {proc_list} in config file'