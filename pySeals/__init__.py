__version__ = '0.0.1a'

_dbpath = "/home/andre/Downloads/MEOP-CTD_2018-04-10/"

# _dbpath = __path__[0] + '/path.cfg'


__all__ = ['load_timesubset']

from .read import (load_timesubset)
