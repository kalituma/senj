from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.graph import GraphManager

class Context:
    def __init__(self, graph_manager:"GraphManager"):
        self._cache = {}
        self._counter = {}
        self._graph_manager:"GraphManager" = graph_manager

        # manager = Manager()
        # self.counter = manager.dict()
        # self.cache = manager.dict()
        # self.lock = Lock()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def cache(self):
        return self._cache

    @property
    def graph_manager(self) -> "GraphManager":
        return self._graph_manager

    @graph_manager.setter
    def graph_manager(self, graph_manager:"GraphManager"):
        self._graph_manager = graph_manager

    def get(self, key):
        return self.cache[key]

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        del self.cache[key]