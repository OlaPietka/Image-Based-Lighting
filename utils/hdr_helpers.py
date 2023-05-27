import numpy as np
import math
from scipy.interpolate import griddata
import scipy.sparse
import scipy.sparse.linalg


def gsolve(Z: np.ndarray, B: np.ndarray, l: int, w) -> (np.ndarray, np.ndarray):
    '''
    Given a set of pixel values observed for several pixels in several
    images with different exposure times, this function returns the
    imaging system’s response function g as well as the log film irradiance
    values for the observed pixels.

    :param Z: N x P array for P pixels in N images
    :param B: is the log delta t, or log shutter speed, for image j
    :param l: lambda, the constant that determines smoothness
    :param w: is the weighting function value for pixel value
    :returns g: solved g value per intensity, of shape 256 x 1
    :returns le: log irradiance for sample pixels of shape P x 1
    '''

    N, P = Z.shape

    n = 256
    A = scipy.sparse.lil_matrix(((N * P) + n + 1, n + P), dtype='double') # init lil
    b = np.zeros((A.shape[0], 1), dtype='double')

    k = 0
    # for each pixel
    for i in range(N):
        # for each image
        for j in range(P):
            wij = w(Z[i, j])
            A[k, Z[i, j]] = wij
            A[k, n + j] = -wij
            b[k, 0] = wij * B[i]
            k += 1

    # Fix the curve by setting its middle value to 0
    A[k, 128] = 1
    k += 1

    # Include the smoothness equation
    for i in range(n - 2):
        A[k, i] = l 
        A[k, i + 1] = -2 * l 
        A[k, i + 2] = l 
        k += 1
    
    x = scipy.sparse.linalg.lsqr(A.tocsr(), b); 

    g = x[0][:n]
    lE = x[0][n:]

    return g, lE

def get_equirectangular_image(reflection_vector, hdr_image):
    '''
    Given a set of Reflection Vectors for all the pixels in the image
    along with the HDR image saved from the previous part, this function 
    returns the equirectangular image for the environment map that can be
    directly used in Blender for the next part.
    :param reflection_vector: H x W x 3 array containing the reflection vector at each pixel across the three dimensions
    :param hdr_image: the LDR merged image from the previous part
    :returns equirectangular_image: This is the equirectangular environment map that is to be used in the next part.
    '''
    
    H, W, C = hdr_image.shape
    rv_x, rv_y, rv_z = np.split(reflection_vector, 3, axis = 2)
    
    theta_ball = math.pi - np.arccos(rv_y)
    phi_ball = np.arctan2(rv_z, rv_x)
    phi_ball[phi_ball != phi_ball] = 0
    phi_ball += 3*math.pi/2
    phi_ball %= 2*math.pi
    
    EH, EW = 360, 720
    phi_1st_half = np.arange(math.pi, 2*math.pi, math.pi / (EW//2))
    phi_2nd_half = np.arange(0*math.pi, math.pi, math.pi / (EW//2))
    
    theta_range = np.arange(0, math.pi, math.pi/EH)
    phi_ranges = np.concatenate((phi_1st_half, phi_2nd_half))
    phis, thetas = np.meshgrid(phi_ranges, theta_range)
    
    spherical_coord = np.concatenate((phi_ball, theta_ball), axis = 2).reshape(-1, 2)
    spherical_vals = hdr_image.reshape(-1, 3)
    equirectangular_coord = np.stack((phis, thetas), axis = 2).reshape(-1, 2)
    equirectangular_intensities = []
    for c in range(C):
        equirectangular_intensity = griddata(spherical_coord, spherical_vals[:,c], equirectangular_coord)
        equirectangular_intensities.append(equirectangular_intensity.reshape(EH, EW))
        equirectangular_image = np.stack(equirectangular_intensities, axis = 2)
    
    
    equirectangular_image[equirectangular_image != equirectangular_image] = equirectangular_image[equirectangular_image == equirectangular_image].mean()
    
    return equirectangular_image.astype(np.float32)
    