from core.util.op import OP_TYPE

class ExtensionNotSupportedError(Exception):
    def __init__(self, module:str, available_exts:list[str], specified_ext:str):
        if specified_ext == '':
            msg = f'No extension specified in {module} module. Available extensions are {available_exts}'

        msg = f'{specified_ext} is not supported in {module} module. Available extensions are {available_exts}'
        super(ExtensionNotSupportedError, self).__init__(msg)

class ExtensionMatchingError(Exception):
    def __init__(self, src_ext:str, tar_ext:str):
        msg = f'{src_ext} is not matched with {tar_ext}'
        super(ExtensionMatchingError, self).__init__(msg)

class NotHaveSameBandShapeError(Exception):
    def __init__(self, raster_name:str):
        msg = f'Band shape is not same in {raster_name}'
        super(NotHaveSameBandShapeError, self).__init__(msg)

class OPTypeNotAvailableError(Exception):
    def __init__(self, op_name:str, set_op:OP_TYPE, available_ops:list):
        super().__init__(f'{str(set_op)} can not be set at "{op_name}". {available_ops} is available')

