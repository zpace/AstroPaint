"""
library containing [projected] halo profiles
"""

__author__ = "Siavash Yasini"
__email__ = "yasini@usc.edu"

from copy import deepcopy
import numpy as np
from . import transform
from astropy import units as u
from astropy.constants import sigma_T, m_p
from astropy.cosmology import Planck15 as cosmo
sigma_T = sigma_T.to(u.Mpc**2).value # [Mpc^2]
m_p = m_p.to(u.M_sun).value # [M_sun]
f_b = cosmo.Ob0/cosmo.Om0
c = 299792. #km/s
T_cmb = 2.7251
Gcm2 = 4.785E-20 #(Mpc/M_sun)

#########################################################
#                       Profiles
#########################################################

# ------------------------
#           3D
# ------------------------

def constant_density(r, constant):

    """
    return a constant value at every input r

    Parameters
    ----------
    r: [Mpc]
        distance from the center
    constant:
        multiplicative constant

    Returns
    -------
    constant

    """

    return constant


def linear_density(r, intercept, slope):

    """
    return a r*constant at every input r

    Parameters
    ----------
    r: [Mpc]
        distance from the center
    intercept:
       intercept of the line
    slope:
        slope of the line

    Returns
    -------
    intercept

    """

    return intercept + r * slope


def mass_density_NFW(r, rho_s, R_s):
    """
    Calculate the NFW profile #TODO: add reference Eq.

    Parameters
    ----------
    r:
        distance from the center
    rho_s:
        density at radius R_s
    R_s:
        characterisic radius R_200c/c_200c

    Returns
    -------
    rho = 4 * rho_s * R_s ** 3 / r / (r + R_s) ** 2
    """

    rho = 4 * rho_s * R_s ** 3 / r / (r + R_s) ** 2

    return rho

# ------------------------
#        Projected
# ------------------------


def mass_density_NFW_proj(r, rho_s, R_s):

    """
    projected NFW mass profile
    Eq. 7 in Bartlemann 1996: https://arxiv.org/abs/astro-ph/9602053

    Returns
    -------
    surface mass density: [M_sun/Mpc^2]
    """

    #FIXME: remove this
    #print("flattening")

    #r = deepcopy(r)
    #r[r < 0.1] = 0.1  # flatten the core

    x = np.asarray(r/R_s, dtype=np.complex)
    f = 1 - 2 / np.sqrt(1 - x ** 2) * np.arctanh(np.sqrt((1 - x) / (1 + x)))
    f = f.real
    f = np.true_divide(f, x ** 2 - 1)
    Sigma = 8 * rho_s * R_s * f
    return Sigma

def tau_density_NFW_proj(r, rho_s, R_s):

    """
    projected NFW tau profile
    Eq. 7 in Battaglia 2016 :

    Returns
    -------
    tau: [NA]
    """
    X_H = 0.76
    x_e = (X_H+1)/2*X_H
    f_s = 0.02
    mu = 4/(2*X_H+1+X_H*x_e)

    Sigma = mass_density_NFW_proj(r, rho_s, R_s)
    tau = sigma_T * x_e * X_H * (1-f_s) * f_b * Sigma / mu / m_p
    return tau

def solid_sphere_proj(r, M_200c, R_200c):
    """
    projected mass density of uniform sphere

    Parameters
    ----------
    r: [Mpc]
        distance from the center
    M_200c: [M_sun]
        total mass of the sphere
    R_200c: [Mpc]
        total radius (edge) of the sphere

    Returns
    -------
    Sigma = M_200c /2/pi * sqrt(R_tot**2 - r**2)/R_tot**3

    """
    Sigma = M_200c / 2 / np.pi * np.sqrt(R_200c ** 2 - r ** 2) / R_200c ** 3

    return Sigma


def deflect_angle_NFW(r, c_200c, R_200c, M_200c, *, suppress=True):
    """
    calculate the deflection angle of a halo with NFW profile
    Use Eq 6 in Baxter et al 2015 (1412.7521)

    Parameters
    ----------
    c_200c:
        halo concentration parameter
    R_200c:
        halo virial radius in [Mpc]
    M_200c:
        virial mass of halo in M_sun
    r:
        distance from the center of halo [Mpc]

    Returns
    -------
        the deflection angle at distance r from the center of halo
    """

    A = M_200c*c_200c**2/(np.log(1+c_200c)-c_200c/(1+c_200c))/4./np.pi
    C = 16*np.pi*Gcm2*A/c_200c/R_200c

    R_s = R_200c / c_200c
    x = r/R_s
    x = x.astype(np.complex)

    f = np.true_divide(1, x) * (np.log(x/2) + 2/np.sqrt(1-x**2) *
                          np.arctanh(np.sqrt(np.true_divide(1-x, 1+x))))

    alpha = C*f

    # suppress alpha at large radii
    if suppress:
        suppress_radius = 8*R_200c
        alpha *= np.exp(-(r/suppress_radius)**3)

    return alpha.real

# ------------------------
#         tests
# ------------------------


def kSZ_T_solid_sphere(r, M_200c, R_200c, v_r, *, T_cmb=T_cmb):

    Sigma = solid_sphere_proj(r, M_200c, R_200c)
    tau = transform.M_to_tau(Sigma)
    dT = -tau * v_r * T_cmb

    return dT


def kSZ_T_NFW(r, rho_s, R_s, v_r, *, T_cmb=T_cmb):

    tau = tau_density_NFW_proj(r, rho_s, R_s)
    dT = -tau * v_r/c * T_cmb

    return dT


def BG_NFW(r, r_hat, c_200c, R_200c, M_200c, th, ph, v_th, v_ph, *, T_cmb=T_cmb):

    alpha = deflect_angle_NFW(r, c_200c, R_200c, M_200c)
    v_vec = transform.convert_velocity_sph2cart(th, ph, 0, v_th, v_ph)
    dT = -alpha * np.dot(r_hat, v_vec)/c * T_cmb

    return dT
