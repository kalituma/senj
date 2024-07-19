# process type
PINIT = 'PINIT'
PEND = 'PEND'
PBRIDGE = 'PBRIDGE'

# operation types
OINIT = 'OINIT'
OEND = 'OEND'

# node types
PR = 'PROCESS'
IP = 'INPUT'
OP = 'OP'

# relationship types
INCLUDE = 'INCLUDE'
GEN = 'GEN'
LINK = 'LINK'

from .graph_build import *
from .graph_query import *

