
class ProductTypeError(Exception):
    def __init__(self, supported_product:list[str], current_product:str):
        msg = f'Product type should be {[t for t in supported_product]} for {self.__str__}, but got {current_product}'
        super(ProductTypeError, self).__init__(msg)

class OperationTypeError(Exception):
    def __init__(self, supported_ops:list[str], current_op:str):
        msg = f'Processor should be initialized with {[t for t in supported_ops]} operations, but got {current_op}'
        super(OperationTypeError, self).__init__(msg)