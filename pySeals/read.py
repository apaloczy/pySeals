# Description: Tools for reading, subsetting and
#              visualizing MEOP in situ data.
# Author:      André Palóczy
# E-mail:      paloczy@gmail.com

import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from datetime import datetime
from xarray import open_dataset, concat, Variable, Dataset
from pandas import Timestamp

__all__ = ['load_subset',
           'strip_profile']


def load_subset(tstart, tend, bbox=None, path='', concatenate=False, interpolated=False,
                adjusted=True, qc=True, mask_qcflags=[9],
                which_vars=['PRES', 'JULD', 'TEMP', 'PSAL']):
    """
    Loads a time-latitude-longitude subset of the full MEOP dataset by searching
    for all tags that fall within the specified [tstart, tend] and
    [lon_west, lon_east, lat_south, lat_north] limits.
    """
    ts, te = tstart, tend
    tstart = Timestamp(tstart).to_pydatetime()
    tend = Timestamp(tend).to_pydatetime()
    kwload = dict(varnames=which_vars, adjusted=adjusted, qc=qc, mask_qcflags=mask_qcflags)
    if interpolated:
        intrp = '_interp'
    else:
        intrp = ""

    DS = None
    cdirs = [d.rstrip('/') for d in glob(path+'/*/')] # Get all country data directories.
    ntags = 0
    for cdir in cdirs:
        fglob = cdir + '/DATA_ncARGO%s/*.nc'%intrp
        fnames = glob(fglob)
        fnames.sort()
        for fname in fnames:
            ds = open_dataset(fname)
            try:
                t = np.array([Timestamp(tn).to_pydatetime() for tn in ds['JULD'].values])
            except TypeError:
                t = np.array([Timestamp(tn.year, tn.month, tn.day, tn.hour, tn.minute, tn.second).to_pydatetime() for tn in ds['JULD'].values])
            in_time = np.logical_and(t>tstart, t<tend)
            if in_time.any():        # Subset of tag is in desired time.
                if bbox is not None: # Subset of tag is in desired lat/lon bounding box.
                    lon = ds['LONGITUDE'].values
                    lat = ds['LATITUDE'].values
                    in_lon = np.logical_and(lon>=bbox[0], lon<=bbox[1])
                    in_lat = np.logical_and(lat>=bbox[2], lat<=bbox[3])
                    in_bbox = np.logical_and(in_lon, in_lat)
                else:
                    in_bbox = np.array([True]*in_time.size)
                if in_bbox.any():
                    ntags+=1
                    c1 = fname.split('/')
                    c1, c2 = c1[-1], c1[-3]
                    print("Loading tag " + c1 + ' ('+c2+')')
                    ds = strip_profile(ds, **kwload)

                    # Subset data points in the tag that fall within the wanted time and bbox.
                    dsattrs = ds.attrs
                    inxyt = np.logical_and(in_time, in_bbox)
                    dsvars = dict()
                    for wvar in ds.data_vars.keys():
                        if ds[wvar].values.ndim==2:
                            dsnew = ds[wvar].values[inxyt, :]
                            dsnew = Variable(('t', 'z'), dsnew)
                        elif ds[wvar].values.ndim==1:
                            dsnew = ds[wvar].values[inxyt]
                            dsnew = Variable(('t'), dsnew)
                        dsvars.update({wvar:dsnew})

                    try:
                        pp = ds['PRES_ADJUSTED'].values[inxyt,:]
                    except KeyError:
                        pp = ds['PRES'].values[inxyt,:]
                    # if interpolated:
                    coords = dict(t=t[inxyt], p=(('t', 'z'), pp))
                    # else:
                    #     coords = dict(t=t[inxyt])
                    #     dsvars.update({'p':pp})
                    ds = Dataset(data_vars=dsvars, coords=coords, attrs=dsattrs)

                    if concatenate: # Concatenate all matching tags in a single section.
                        if DS is None:
                            DS = ds
                        else:
                            if interpolated:
                                DS = concat((DS, ds), dim='t')
                            else: # FIXME. Implement concatenation for non-interpolated data. But maybe it is not a good strategy.
                                raise NotImplementedError

                    else: # Add tag as a dictionary entry.
                        tag = fname.split('/')[-1].split('_')[0]
                        ds.attrs = dsattrs
                        if DS is None:
                            DS = {tag:ds}
                        else:
                            DS.update({tag:ds})

    print("")
    if bbox is None:
        print("Found %d tags between %s and %s."%(ntags, ts, te))
    else:
        print("Found %d tags between %s and %s in bbox [%.1f, %.1f, %.1f, %.1f]."%(ntags, ts, te,
                                                                               bbox[0], bbox[1],
                                                                               bbox[2], bbox[3]))

    return DS


def strip_profile(ds, varnames=['PRES', 'TEMP', 'PSAL'], adjusted=True, qc=True, mask_qcflags=[9]):
    """
    Return an xarray.Dataset object containing only the
    wanted variables, with the specified QC flags
    masked out (if qc=True).
    """
    keep = ['JULD', 'LONGITUDE', 'LATITUDE']
    if qc:
        keep.append('JULD_QC')
        keep.append('POSITION_QC')
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
                try:
                    ds[v] = ds[v].where(ds[qcarr]!=qctag)
                except KeyError:
                    continue

    if adjusted:
        presvar = 'PRES_ADJUSTED'
    else:
        presvar = 'PRES'

    ds = ds.set_coords(['JULD',presvar])
    ds = ds.set_index(indexes=dict(N_PROF='JULD'))

    return ds
