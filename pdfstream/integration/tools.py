"""The functions used in the integration pipelines. All functions consume namespace and return the modified
namespace. """
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy import ndarray
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from xpdtools.tools import generate_binner, mask_img

__all__ = ['bg_sub', 'auto_mask', 'integrate', 'vis_chi', 'vis_img']

# default mask_img auto mask setting
_AUTOMASK_SETTING = dict(
    alpha=2.0
)
# default pyfai integration setting
_INTEG_SETTING = dict(
    npt=1480,
    correctSolidAngle=False,
    method='csr',
    unit='q_A^-1',
    safe=False
)
# default visualization setting
_LABEL = {
    "q_A^-1": r"Q ($\mathrm{\AA}^{-1}$)",
    "q_nm^-1": r"Q ({nm}$^{-1}$)",
    "2th_deg": r"2$\theta$ (deg)",
    "2th_rad": r"2$\theta$ (rad)",
    "r_mm": r"radius (mm)"
}


def bg_sub(img: ndarray, bg_img: ndarray, bg_scale: float = None) -> ndarray:
    """Subtract the background image from the data image inplace.

    Parameters
    ----------
    img : ndarray
        The 2D diffraction image array.

    bg_img : ndarray
        The 2D background image array.

    bg_scale : float
        The scale of the the background image.
    """
    if bg_scale is None:
        bg_scale = 1.
    if bg_img.shape != img.shape:
        raise ValueError(f"Unmatched shape between bg_img and img: {bg_img.shape}, {img.shape}.")
    img = img - bg_scale * bg_img
    return img


def auto_mask(img: ndarray, ai: AzimuthalIntegrator, mask_setting: dict = None) -> Tuple[ndarray, dict]:
    """Automatically generate the mask of the image.

    Parameters
    ----------
    img : ndarray
        The 2D diffraction image array.

    ai : AzimuthalIntegrator
        The AzimuthalIntegrator instance.

    mask_setting : dict
        The user's modification to auto-masking settings.

    Returns
    -------
    mask : ndarray
        The mask as a boolean array. True pixels are good pixels, False pixels are masked out.

    _mask_setting : dict
        The whole mask_setting.
    """
    _mask_setting = _AUTOMASK_SETTING.copy()
    if mask_setting is not None:
        _mask_setting.update(mask_setting)
    binner = generate_binner(ai, img.shape)
    mask = np.invert(mask_img(img, binner, **_mask_setting))
    return mask, _mask_setting


def integrate(
        img: ndarray, ai: AzimuthalIntegrator, mask: ndarray = None, integ_setting: dict = None
) -> Tuple[ndarray, dict]:
    """Use AzimuthalIntegrator to integrate the image.

    Parameters
    ----------
    img : ndarray
        The 2D diffraction image array.

    ai : AzimuthalIntegrator
        The AzimuthalIntegrator instance.

    mask : ndarray
        The mask as a boolean array. True pixels are good pixels, False pixels are masked out.

    integ_setting : dict
        The user's modification to integration settings.

    Returns
    -------
    chi : ndarray
        The chi data. The first row is bin centers and the second row is the average intensity in bins.

    _integ_setting: dict
        The whole integration setting.
    """
    # merge integrate setting
    _integ_setting = _INTEG_SETTING.copy()
    if mask is not None:
        _integ_setting.update(dict(mask=mask))
    if integ_setting is not None:
        _integ_setting.update(integ_setting)
    # integrate
    chi = np.stack(
        ai.integrate1d(img, **_integ_setting)
    )
    return chi, _integ_setting


def vis_img(img: ndarray, mask: ndarray = None, img_setting: dict = None) -> Axes:
    """Visualize the processed image. The color map will be determined by statistics of the pixel values. The color map
    is determined by mean +/- z_score * std.

    Parameters
    ----------
    img : ndarray
        The 2D diffraction image array.

    mask: ndarray
        The whole integration setting.

    img_setting : dict
        The user's modification to imshow kwargs except a special key 'z_score'.

    Returns
    -------
    ax : Axes
        The axes with the image shown.
    """
    if img_setting is None:
        img_setting = dict()
    fig = plt.figure()
    ax: Axes = fig.add_subplot(111)
    if mask is not None:
        img = np.ma.masked_array(img, mask)
    mean, std = img.mean(), img.std()
    z_score = img_setting.pop('z_score', 2.)
    kwargs = {
        'vmin': mean - z_score * std,
        'vmax': mean + z_score * std
    }
    kwargs.update(**img_setting)
    img_obj = ax.imshow(img, **kwargs)
    ax.axis("off")
    # color bar with magical settings to make it same size as the plot
    plt.colorbar(img_obj, ax=ax, fraction=0.046, pad=0.04)
    plt.show(block=False)
    return ax


def vis_chi(chi: ndarray, plot_setting: dict = None, unit: str = None) -> Axes:
    """Visualize the chi curve.

    Parameters
    ----------
    chi : ndarray
        The chi data. The first row is bin centers and the second row is the average intensity in bins.

    plot_setting : dict
        The kwargs for the plot function.

    unit: str
        The unit of the chi data. It affects the label of the plot. If None, no unit.

    Returns
    -------
    ax : Axes
        The axes with the curve plotted.
    """
    if plot_setting is None:
        plot_setting = dict()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(chi[0], chi[1], **plot_setting)
    if unit:
        ax.set_xlabel(_LABEL.get(unit))
    ax.set_ylabel('I (A. U.)')
    plt.show(block=False)
    return ax