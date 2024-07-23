class BandError(Exception):
    def __init__(self, bands:list[str]):
        if len(bands) == 0:
            msg = 'No band names found in the product'
        else:
            msg = f'No band names found in the product : {bands}'
        super(BandError, self).__init__(msg)

class ModuleError(Exception):
    def __init__(self, module:str, available_modules:list[str]):
        msg = f'"{module}" module is not supported. Available modules are {available_modules}'
        super(ModuleError, self).__init__(msg)

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

