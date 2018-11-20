__version__ = '0.0.1a'
_dbpath = __path__[0] + '/path.cfg'

with open(_dbpath) as f:
    _dbpath = f.readlines()[0].strip()


__all__ = ['load_timesubset',
           'strip_profile']

from .read import (load_timesubset,
                   strip_profile)
