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


def load_timesubset(tstart, tend, concatenate=False, path=_dbpath, interpolated=True,
                    adjusted=True, qc=True, mask_qcflags=[9],
                    which_vars=['PRES', 'JULD', 'TEMP', 'PSAL']):
    ts, te = tstart, tend
    tstart = Timestamp(tstart).to_pydatetime()
    tend = Timestamp(tend).to_pydatetime()
    kwload = dict(varnames=which_vars, adjusted=adjusted, qc=qc, mask_qcflags=mask_qcflags)
    if interpolated:
        intrp = '_interp'
    else:
        intrp = ""

    DS = None
    cdirs = [d.rstrip('/') for d in glob(path+'*/')]
    ntags = 0
    for cdir in cdirs:
        fglob = cdir + '/DATA_ncARGO%s/*.nc'%intrp
        fnames = glob(fglob)
        fnames.sort()
        for fname in fnames:
            ds = open_dataset(fname)
            t = np.array([Timestamp(tn).to_pydatetime() for tn in ds['JULD'].values])
            ftime = np.logical_and(t>tstart, t<tend)
            if ftime.any(): # Subset of tag is in desired time.
                ntags+=1
                c1 = fname.split('/')
                c1, c2 = c1[-1], c1[-3]
                print("Loading tag " + c1 + ' ('+c2+')')
                ds = strip_profile(ds, **kwload)

                if concatenate: # Concatenate all matching tags in a single section.
                    if DS is None:
                        DS = ds
                    else:
                        DS = concat((DS, ds), dim='N_PROF')
                else: # Add tag as a dictionary entry.
                    tag = fname.split('/')[-1].split('_')[0]
                    if DS is None:
                        DS = {tag:ds}
                    else:
                        DS.update({tag:ds})

    print("")
    print("Found %d tags between %s and %s."%(ntags, ts, te))

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

    # Apply the specified QC tag(s).
    if qc:
        qcarr = v + '_QC'
        k = [a for a in ds.data_vars.keys() if '_QC' not in a]
        for v in k:
            for qctag in mask_qcflags:
                ds[v] = ds[v].where(ds[qcarr]!=qctag)

    if adjusted:
        presvar = 'PRES_ADJUSTED'
    else:
        presvar = 'PRES'

    ds = ds.set_coords(['JULD',presvar])
    ds = ds.set_index(indexes=dict(N_PROF='JULD'))

    return ds
