from multiprocessing import Manager, Lock

class Context:
    def __init__(self):
        self.cache = {}
        self.counter = {}
        # manager = Manager()
        # self.counter = manager.dict()
        # self.cache = manager.dict()
        # self.lock = Lock()