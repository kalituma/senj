from core.util import import_lazy

def import_snappy():
    return import_lazy('esa_snappy', 'esa_snappy')
