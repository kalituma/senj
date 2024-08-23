class ContainedBandError(Exception):
    def __init__(self, bands:list[str]):
        if len(bands) == 0:
            msg = 'No band names found in the product'
        else:
            msg = f'No band names found in the product : {bands}'
        super(ContainedBandError, self).__init__(msg)

class ModuleError(Exception):
    def __init__(self, module:str, available_modules:list[str]):
        msg = f'"{module}" module is not supported. Available modules are {available_modules}'
        super(ModuleError, self).__init__(msg)

