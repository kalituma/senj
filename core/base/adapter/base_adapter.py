from abc import ABC, abstractmethod

class BaseAdapter(ABC):    

    @abstractmethod
    def read_data(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_data(self, *args, **kwargs):
        pass