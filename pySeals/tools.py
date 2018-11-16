import numpy as np
import matplotlib.pyplot as plt

def derive_gsw():
    return NotImplementedError

def plt_traj(ds):
    """Plot the trajectory of a MEOP tag."""
    plt.plot(ds['LONGITUDE'], ds['LATITUDE'])


def get_basemap():
    fig, ax = plt.subplots()
    # Cartopy
    return fig, ax
