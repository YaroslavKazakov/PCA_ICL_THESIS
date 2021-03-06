"""
This code was created by Iaroslav Kazakov, an Aeronautical student at Imperial College London on 9/11/2020
as part of his Final Year Project.
The data used to recreate a POD analysis is taken from a research paper and cannot be shared with public unless
author's permission is granted.
This code is the first goal set up during a meeting on 9/11/20, whereby classic and snapshot PODs need to
be reproduced for a given data set.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pickle
import scipy.linalg as la
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
"""
Note how the data is distributed it is in the form of (2000, 384, 192, 2), i.e. there are 2000 x 2 2D matrices
where each of these 2000 x 2 matrices contain a velocity (either vertical or horizontal) vector at every grid point.
The grid is asymmetric, it has twice as many points in one direction that the other one.
"""

def velocities_upload(filename='flow_field_data0.pickle', comp=2):
    """

    filename: load the pickle file
    comp: indicate the number of velocity components
    return: two 3D ndarrays where the 0 axis corresponds to the temporal observation and
    axis 1,2 relate to the spatial observation on the grid
    """
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    for i in range(comp):
        if i==0:
          U = data[:, :, :, i]
        elif i==1:
          V = data[:, :, :, i]
    return U,V


def velocity_dash_2D(U,V):
    """
    1. specify two 3D ndarrays velocities from which the fluctuations have to be derived
    2. reshape the matrices such that the spatial points are stretched out in a single row, i.e. obtain a 2D matrix
    3. concatenate the matrices together
    """
    U_dash = (U-np.mean(U, axis=0)).reshape(U.shape[0], U.shape[1]*U.shape[2], order='F')
    V_dash = (V-np.mean(V, axis=0)).reshape(V.shape[0], V.shape[1]*V.shape[2], order='F')
    Vel_dash = np.concatenate((U_dash, V_dash), axis=1)
    return Vel_dash


def eig(Vel_dash, points=250, cutoff=20):
    """
    Nested function that calculates eigenvalues and eigenvectors
    ASSUMPTION: The observed flow is NOT periodic, otherwise choose the values corresponding to one full period only
    :param Vel_dash: Input concatenated velocity fluctuations
    :param points: define the step points
    :param cutoff: define the threshold for eigenvalue cutoff point
    :return: eigenvalue, eigenvector and Vel_dash_Transpose
    """
    def sub_eig(V = Vel_dash, step = points):
      V_T = V.transpose()[:, :1999:step]
      R = np.dot(V[:1999:step, :], V_T)
      eigvals, eigvecs = la.eig(R)
      return eigvals, eigvecs, V_T

    eigvals, eigvecs, Vel_dash_T = sub_eig()
    indices = [i for i in range(eigvals.shape[0]) if eigvals[i] <= cutoff]
    eigval = np.delete(eigvals, np.where(eigvals <= cutoff))
    eigvec = np.delete(eigvecs, indices, 1)
    return eigval, eigvec, Vel_dash_T


def all_modes(eigval,eigvec,V):
       mod = np.dot(eigvec, np.diag(eigval.real**(-0.5)))
       modes = np.dot(V, mod)
       def rec_modes(modes=modes,V= V):
           a = np.array([0]*np.shape(modes)[1], dtype=float)
           for i in range(np.shape(modes)[1]):
               a[i] = np.inner(V[:, i], modes[:, i])
               modes[:, i] = a[i] * modes[:, i]
           return modes, a
       recreated_modes, a_coeff = rec_modes()
       return modes, recreated_modes, a_coeff


def grid (dy = 1 / 383,dx = 1 / 191):
    y, x = np.mgrid[slice(0, 1 + dy, dy), slice(0, 1 + dx, dx)]
    return y, x


def recreation_plot(recreated_modes):
    U = recreated_modes.sum(axis=1)
    U_POD = np.array(U[:int(len(U) / 2)])
    U_POD = U_POD.reshape(384, 192, order='F')
    return U_POD


def mode_decomposition(n,modes):
    Velocity = np.empty([384, 192, n])
    for i in range(n):
        Velocity[:, :, i] = np.array(modes[:, i][:int(len(modes[:, i]) / 2)]).reshape(384, 192, order='F')
    return Velocity


def level_norm(data):
    level = MaxNLocator(nbins=100).tick_values(data.min(), data.max())
    norm = BoundaryNorm(level, ncolors=cmap.N, clip=True)
    return norm


def plot(x, y, data, N, cmap, norm):
    fig, ax = plt.subplots(1)
    cf = ax.contourf(y, x, data, cmap=cmap, norm=norm)
    fig.colorbar(cf, ax=ax)
    mode= 'Mode ' + str(N)
    ax.set_title(mode)
    return ax


U, V = velocities_upload()
Vel_dash = velocity_dash_2D(U, V)
eigval, eigvec, Vel_dash_T = eig(Vel_dash, points=100)
modes, recreated_modes, a_coeff = all_modes(eigval, eigvec, Vel_dash_T)
y, x = grid()
cmap = plt.get_cmap('seismic')
U_full = recreation_plot(recreated_modes)
level_full, norm_full = level_norm(U_full)
Velocity = mode_decomposition(4, modes)
norm1 = level_norm(Velocity[:, :, 0])
norm2 = level_norm(Velocity[:, :, 1])
norm3 = level_norm(Velocity[:, :, 2])
norm4 = level_norm(Velocity[:, :, 3])
ax0 = plot(x, y, U_full, 'Reconstructed', cmap, norm_full)
ax = plot(x, y, Velocity[:, :, 0], 1, cmap,norm1)
ax1 = plot(x, y, Velocity[:, :, 1], 2, cmap,norm2)
ax2 = plot(x, y, Velocity[:, :, 2], 3, cmap,norm3)
ax3 = plot(x, y, Velocity[:, :, 3], 4, cmap,norm4)
plt.show()
