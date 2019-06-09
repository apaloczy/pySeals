import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy as ctpy
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from seawater import ptmp, dens


def plt_traj(ds, fig=None, bbox=None, **kw):
    """
    Plot the trajectory of a MEOP tag. Keyword arguments
    are map options passed to bmap(). If bbox=None (default)
    infers the lon, lat limits for the figure from the dataset.
    """
    if fig is None:
        fig = plt.figure()

    if bbox is None:
        bbox = [ds['LONGITUDE'].values.min(), ds['LONGITUDE'].values.max(),
                ds['LATITUDE'].values.min(), ds['LATITUDE'].values.max()]

    ax = bmap(fig, bbox, **kw)
    ax.scatter(ds['LONGITUDE'], ds['LATITUDE'], s=1.0)

    return fig, ax


def plt_TS(ds, fig=None, s=0.2, c='k', pr=0):
  if fig is None:
    fig, ax = plt.subplots()

  if isinstance(ds, dict): # Non-interpolated data comes in a dictionary of datasets.
    S, T, p = np.array([]), np.array([]), np.array([])
    for dsi in ds.values():
      try:
        S = np.concatenate((S, dsi['PSAL_ADJUSTED'].values.ravel()))
      except KeyError:
        S = np.concatenate((S, dsi['PSAL'].values.ravel()))
      try:
        T = np.concatenate((T, dsi['TEMP_ADJUSTED'].values.ravel()))
      except KeyError:
        T = np.concatenate((T, dsi['TEMP'].values.ravel()))
      p = np.concatenate((p, dsi['p'].values.ravel()))
  else:
    try:
      S = ds['PSAL_ADJUSTED'].values.ravel()
    except KeyError:
      S = ds['PSAL'].values.ravel()
    try:
      T = ds['TEMP_ADJUSTED'].values.ravel()
    except KeyError:
      T = ds['TEMP'].values.ravel()
    p = ds['p'].values.ravel()

  T = ptmp(S, T, p, pr=pr)

  ax.scatter(S, T, s=s, c=c, zorder=9)
  Sx = np.linspace(np.nanmin(S)-0.5, np.nanmax(S)+0.5, 1000)
  Ty = np.linspace(np.nanmin(T)-0.5, np.nanmax(T)+0.5, 1000)
  Sx, Ty = np.meshgrid(Sx, Ty)
  sigi = dens(Sx, Ty, pr) - 1000
  cc = ax.contour(Sx, Ty, sigi, levels=np.arange(0, 40, 0.1), colors='gray', zorder=-9)
  ax.clabel(cc, manual=False, fmt='%.1f', inline_spacing=0.01)
  ax.set_xlabel(r'Practical Salinity [unitless]')
  ax.set_ylabel(r'Potential Temperature [$^o$C]')
  ax.set_xlim((np.nanmin(S)-0.05, np.nanmax(S)+0.05))
  ax.set_ylim((np.nanmin(T)-0.2, np.nanmax(T)+0.2))

  return fig, ax


def bmap(fig, bbox, proj=ccrs.PlateCarree(), xticks=None, yticks=None,
                                             dlon=5, dlat=2, land=None, coastlines=True):
    ax = fig.add_subplot(111, projection=proj)
    ax.set_extent(bbox, proj)

    if land is None:
        land = ctpy.feature.LAND
    ax.add_feature(land, zorder=999)

    if coastlines:
        ax.coastlines('10m')

    if not xticks:
        xticks = np.arange(bbox[0], bbox[1], dlon)
    if not yticks:
        yticks = np.arange(bbox[2], bbox[3], dlat)

    gl = ax.gridlines(crs=ccrs.PlateCarree(),
                      linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.xlabels_bottom = True
    gl.ylabels_right = False
    gl.xlines = True
    gl.ylines = True
    gl.xlocator = mticker.FixedLocator(xticks)
    gl.ylocator = mticker.FixedLocator(yticks)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 10, 'color': 'gray'}
    gl.ylabel_style = {'size': 10, 'color': 'gray'}

    return ax
