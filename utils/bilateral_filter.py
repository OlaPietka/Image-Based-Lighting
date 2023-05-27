import numpy as np
import math
from scipy.interpolate import interpn, LinearNDInterpolator
from scipy.ndimage import convolve



def bilateral_filter(data: np.ndarray, edge=None,
                     edge_min=None, edge_max=None,
                     sigma_spatial=None, sigma_range=None,
                     sampling_spatial=None, sampling_range=None) -> np.ndarray:
    '''
    Bilateral and Cross-Bilateral Filter using the Bilateral Grid.
    '''
    assert len(data.shape) == 2

    # assign edge iff not assigned
    if(edge is None):
        edge = data

    assert len(edge.shape) == 2
    IH, IW = data.shape

    # setup parameters
    if(edge_min is None):
        edge_min = edge.min()
    if(edge_max is None):
        edge_max = edge.max()

    edge_delta = edge_max - edge_min

    if sigma_spatial is None:
        sigma_spatial = min(IW, IH) / 16

    if sigma_range is None:
        sigma_range = 0.1 * edge_delta

    if sampling_spatial is None:
        sampling_spatial = sigma_spatial

    if sampling_range is None:
        sampling_range = sigma_range

    assert edge.shape == data.shape

    # setup local parameters

    # parameters
    derived_sigma_spatial = sigma_spatial / sampling_spatial
    derived_sigma_range = sigma_range / sampling_range

    padding_xy = math.floor(2 * derived_sigma_spatial) + 1
    padding_z = math.floor(2 * derived_sigma_range) + 1

    # allocate 3D grid
    DW = math.floor((IW - 1) / sampling_spatial) + 1 + 2 * padding_xy
    DH = math.floor((IH - 1) / sampling_spatial) + 1 + 2 * padding_xy
    DZ = math.floor(edge_delta / sampling_range) + 1 + 2 * padding_z

    grid_data = np.zeros((DH, DW, DZ), dtype=np.double)
    grid_weights = np.zeros((DH, DW, DZ), dtype=np.double)

    ww, hh = np.meshgrid(range(IW), range(IH))

    dh = (np.round(hh / sampling_spatial) + padding_xy).astype(np.int)
    dw = (np.round(ww / sampling_spatial) + padding_xy).astype(np.int)
    dz = (np.round((edge - edge_min) / sampling_range) + padding_z).astype(np.int)

    dhf = dh.flatten()
    dwf = dw.flatten()
    dzf = dz.flatten()
    ddf = data.flatten()
    
    for k in range(dz.size):
        dhk = dhf[k]
        dwk = dwf[k]
        dzk = dzf[k]
        dataZ = ddf[k]
        if (dataZ is not None) and (dataZ != float('nan')):
            grid_data[dhk, dwk, dzk] += dataZ
            grid_weights[dhk, dwk, dzk] += 1

    # make gaussian kernel
    KW = int(2 * derived_sigma_spatial + 1)
    KH = KW
    KD = int(2 * derived_sigma_range + 1)

    halfKW = KW // 2
    halfKH = KH // 2
    halfKD = KD // 2

    gridX, gridY, gridZ = np.meshgrid(range(KW), range(KH), range(KD))
    gridX = gridX - halfKW
    gridY = gridY - halfKH
    gridZ = gridZ - halfKD

    gridRSquared = (gridX ** 2 + gridY ** 2) / (derived_sigma_spatial ** 2) +\
        (gridZ ** 2) / (derived_sigma_range ** 2)

    kernel = np.exp(-0.5 * gridRSquared)

    # convolve
    blurredGridData = convolve(grid_data, kernel, mode='constant')
    blurredGridWeights = convolve(grid_weights, kernel, mode='constant')

    # divide
    # avoid divide by 0, won't read there anyway
    blurredGridWeights[blurredGridWeights == 0] = -2
    normalizedBlurredGrid = blurredGridData / blurredGridWeights

    # put 0s where it's undefined
    normalizedBlurredGrid[blurredGridWeights < -1] = 0

    # upsample
    # meshgrid does x, then y, so output arguments need to be reversed
    # hh, ww = np.meshgrid(range(IH), range(IW))
    ww, hh = np.meshgrid(range(IW), range(IH))

    # no rounding
    dh = (hh / sampling_spatial) + padding_xy
    dw = (ww / sampling_spatial) + padding_xy
    dz = (edge - edge_min) / sampling_range + padding_z

    # interpn takes rows, then cols, etc
    # i.e. size(v,1), then size(v,2), ...
    values = normalizedBlurredGrid
    points = np.stack(values.nonzero(), axis=-1)
    values = normalizedBlurredGrid[points[:, 0], points[:, 1], points[:, 2]]
    targets = np.stack((dh, dw, dz), axis=2)
    intp = LinearNDInterpolator(points, values)
    output = intp(targets)

    return output
