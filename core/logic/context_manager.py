from typing import TYPE_CHECKING
from core.logic.context import Context

if TYPE_CHECKING:
    from core.graph import GraphManager

class ContextManager:
    def __init__(self, context:Context):
        self._context:Context = context
        self._graph_manager:"GraphManager" = context.graph_manager

    def add_ops_to_context(self, proc_name, ops):
        self._context.cache[proc_name] = ops

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context:Context):
        self._context = context
