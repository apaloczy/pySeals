# Description: Tools for reading, subsetting and
#              visualizing MEOP in situ data.
# Author:      André Palóczy
# E-mail:      paloczy@gmail.com

import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from datetime import datetime
from xarray import open_dataset, concat
from pandas import Timestamp

from . import _dbpath

__all__ = ['load_timesubset',
           'strip_profile']


def load_timesubset(tstart, tend, path=_dbpath, interpolated=True, adjusted=True,
                    qc=True, mask_qcflags=[9], which_vars=['PRES', 'JULD', 'TEMP', 'PSAL']):
    tstart = Timestamp(tstart).to_pydatetime()
    tend = Timestamp(tend).to_pydatetime()
    kwload = dict(varnames=which_vars, adjusted=adjusted, qc=qc, mask_qcflags=mask_qcflags)
    if interpolated:
        intrp = '_interp'
    else:
        intrp = ""

    DS = None
    cdirs = [d.rstrip('/') for d in glob(path+'*/')]
    for cdir in cdirs:
        fglob = cdir + '/DATA_ncARGO%s/*.nc'%intrp
        fnames = glob(fglob)
        fnames.sort()
        for fname in fnames:
            ds = open_dataset(fname)
            t = np.array([Timestamp(tn).to_pydatetime() for tn in ds['JULD'].values])
            ftime = np.logical_and(t>tstart, t<tend)
            if ftime.any(): # Subset of tag is in desired time.
                c1 = fname.split('/')
                c1, c2 = c1[-1], c1[-3]
                print("Loading tag " + c1 + ' ('+c2+')')
                ds = strip_profile(ds, **kwload)
                if DS is None:
                    DS = ds
                else:
                    DS = concat((DS, ds), dim='N_PROF')

    return DS

def strip_profile(ds, varnames=['PRES', 'TEMP', 'PSAL'], adjusted=True, qc=True, mask_qcflags=[9]):
    """
    Return an xarray.Dataset object containing only the
    wanted variables, with the specified QC flags
    masked out (if qc=True).
    """
    keep = ['JULD']
    if qc:
        keep.append('JULD_QC')
    for v in varnames:
        if adjusted and v not in ['JULD']:
            v += '_ADJUSTED'
            vadjerr = v + '_ERROR'
            keep.append(v)
            keep.append(vadjerr)
        if qc:
            v += '_QC'
        keep.append(v)

    for v in ds.data_vars.keys():
        if v not in keep:
            ds = ds.drop(v)

    if qc:
        qcflags = v + '_QC'

    if adjusted:
        presvar = 'PRES_ADJUSTED'
    else:
        presvar = 'PRES'

    ds = ds.set_coords(['JULD',presvar])
    ds = ds.set_index(indexes=dict(N_PROF='JULD'))

    return ds
