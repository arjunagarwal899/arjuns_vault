import math

import numpy as np
import SimpleITK as sitk
import skimage
import skimage.segmentation
from ipywidgets import interact, widgets
from matplotlib import cm, patches
from matplotlib import pyplot as plt


def plot_scans(img_arr_list, title_list=None, colors_legend=None, rows=None, cols=None, expand_dims=False, cmap="gray"):
    """
    Plot multiple 3D scans in jupyter which can be scrolled through simultaneously

    Args:
        img_arr_list (list): All the scans to plot
        title_list (list, optional): Titles of each of the plots to be displayed. Defaults to None.
        colors_legend (dict(color, label), optional): Tuple of annotation colors and their respective legend names.
            Defaults to None.
        rows (int, optional): Number of rows to use to plot all the scans. 1 row is used by default. Defaults to None.
        cols (int, optional): Number of cols to use to plot all the scans. Defaults to None.
        expand_dims (bool, optional): If a 2D input is given, it will expand it to a 3D by adding an axis at index 0.
            Defaults to False.
    """

    if title_list is None:
        title_list = [""] * len(img_arr_list)
    if not isinstance(img_arr_list, (tuple, list)):
        img_arr_list = [img_arr_list]
    if not isinstance(title_list, (tuple, list)):
        title_list = [title_list]
    if isinstance(cmap, str):
        cmap = [cmap] * len(img_arr_list)

    for i in range(len(img_arr_list)):
        if isinstance(img_arr_list[i], sitk.Image):
            img_arr_list[i] = sitk.GetArrayFromImage(img_arr_list[i])
        if expand_dims:
            if img_arr_list[i].ndim == 2:
                img_arr_list[i] = np.expand_dims(img_arr_list[i], 0)

    if rows is None and cols is None:
        rows = 1
        cols = len(img_arr_list)
    elif rows is None:
        rows = math.ceil(len(img_arr_list) / cols)
    elif cols is None:
        cols = math.ceil(len(img_arr_list) / rows)

    handles = []
    if colors_legend is not None:
        for color, label in colors_legend:
            handles.append(patches.Patch(color=color, label=label))

    def show_layout(z=None):
        fig, ax = plt.subplots(rows, cols, figsize=(7 * cols, 4 * cols), squeeze=False)

        for idx in range(len(img_arr_list)):
            if z is None:
                img = img_arr_list[idx][0]
            else:
                img = img_arr_list[idx][z]

            ax[idx // cols][idx % cols].imshow(img, cmap=cmap[idx])
            ax[idx // cols][idx % cols].title.set_text(title_list[idx])
            ax[idx // cols][idx % cols].axis("off")
            ax[idx // cols][idx % cols].grid(False)

        if colors_legend is not None:
            fig.legend(handles=handles)

        fig.tight_layout()
        fig.show()

    if any([img.ndim >= 3 for img in img_arr_list]):
        interact(
            show_layout,
            z=widgets.IntSlider(
                value=0,
                min=0,
                max=(img_arr_list[0].shape[0] - 1),
                step=1,
            ),
        )
    else:
        show_layout()


def get_annotated_scan(
    img_arr: np.ndarray, mask_arrs: list[np.array], return_colors: bool = False, colors_labels: list = [], **kwargs
):
    """
    Returns an annotated scan given a base scan and a mask of the same size

    Args:
        img_arr (np.ndarray or sitk.Image): Base image
        mask_arrs (list[np.ndarray or sitk.Image]): Masks. Each should be of the same size as img_arr

    Returns:
        np.ndarray: Annotated scan
    """

    if isinstance(img_arr, sitk.Image):
        img_arr = sitk.GetArrayFromImage(img_arr)
    for i in range(len(mask_arrs)):
        if isinstance(mask_arrs[i], sitk.Image):
            mask_arrs[i] = sitk.GetArrayFromImage(mask_arrs[i]).astype(int)

    colors = cm.get_cmap("hsv")(np.linspace(0, 1, len(mask_arrs), endpoint=False))

    orig_dim = img_arr.ndim
    if orig_dim == 2:
        img_arr = np.expand_dims(img_arr, 0)
    assert img_arr.ndim == 3, "Image should be 3D"

    img_arr = (img_arr - img_arr.min() + 1e-6) / (img_arr.max() - img_arr.min() + 1e-6)

    annotated_scan = list(img_arr)
    for mask_arr, color in zip(mask_arrs, colors):
        for i, mask_slc in zip(range(len(annotated_scan)), mask_arr):
            annotated_scan[i] = skimage.segmentation.mark_boundaries(
                annotated_scan[i], mask_slc, color=color[:3], **kwargs
            )
    annotated_scan = np.stack(annotated_scan)

    if orig_dim == 2:
        annotated_scan = np.squeeze(annotated_scan, 0)

    annotated_scan = np.clip(annotated_scan, 0, 1)

    if return_colors:
        colors_legend = list(zip(colors, colors_labels))
        return annotated_scan, colors_legend
    return annotated_scan
