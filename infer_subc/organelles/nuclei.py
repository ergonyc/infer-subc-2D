import numpy as np
from typing import Union, Dict
from pathlib import Path
import time

from skimage.morphology import binary_dilation, binary_erosion 

from infer_subc.core.file_io import (
    export_inferred_organelle,
    import_inferred_organelle,
    import_inferred_organelle_AICS,
)
from infer_subc.core.img import (
    fill_and_filter_linear_size,
    apply_log_li_threshold,
    select_channel_from_raw,
    scale_and_smooth,
    apply_mask,
    get_interior_labels,
    label_uint16,
)
from infer_subc.constants import NUC_CH


##########################
#  infer_nuclei_fromlabel
##########################
def infer_nuclei_fromlabel(in_img: np.ndarray, 
                           nuc_ch: Union[int,None],
                           median_size: int, 
                           gauss_sigma: float,
                           thresh_factor: float,
                           thresh_min: float,
                           thresh_max: float,
                           min_hole_width: int,
                           max_hole_width: int,
                           small_obj_width: int,
                           fill_filter_method: str
                           ) -> np.ndarray:
    """
    Procedure to infer nuclei from linearly unmixed input.

    Parameters
    ------------
    in_img: np.ndarray
        a 3d image containing all the channels (CZYX)
    nuc_ch:
        index of the nuc channel in the input image
    median_size: int
        width of median filter for signal
    gauss_sigma: float
        sigma for gaussian smoothing of  signal
    thresh_factor: float
        adjustment factor for log Li threholding
    thresh_min: float
        abs min threhold for log Li threholding
    thresh_max: float
        abs max threhold for log Li threholding
    min_hole_w: 
        minimum size for hole filling for cellmask signal post-processing
    max_hole_w: 
        hole filling cutoff for nuclei signal post-processing
    small_obj_w: 
        minimum object size cutoff for nuclei signal post-processing
    fill_filter_method:
        determines if small hole filling and small object removal should be run 'sice-by-slice' or in '3D'

    Returns
    -------------
    nuclei_object
        mask defined extent of NU
    
    """
    ###################
    # EXTRACT
    ###################                
    nuclei = select_channel_from_raw(in_img, nuc_ch)

    ###################
    # PRE_PROCESSING
    ###################                
    nuclei =  scale_and_smooth(nuclei,
                        median_size = median_size, 
                        gauss_sigma = gauss_sigma)

    ###################
    # CORE_PROCESSING
    ###################
    nuclei_object = apply_log_li_threshold(nuclei, 
                                           thresh_factor=thresh_factor, 
                                           thresh_min=thresh_min, 
                                           thresh_max=thresh_max)

    ###################
    # POST_PROCESSING
    ###################
    nuclei_object = fill_and_filter_linear_size(nuclei_object, 
                                                hole_min=min_hole_width, 
                                                hole_max=max_hole_width, 
                                                min_size=small_obj_width,
                                                method=fill_filter_method)

    nuclei_labels = label_uint16(nuclei_object)
 
    return nuclei_labels


##########################
#  fixed_infer_nuclei
##########################
def fixed_infer_nuclei_fromlabel(in_img: np.ndarray) -> np.ndarray:
    """
    Procedure to infer cellmask from linearly unmixed input, with a *fixed* set of parameters for each step in the procedure.  i.e. "hard coded"

    Parameters
    ------------
    in_img: np.ndarray
        a 3d image containing all the channels
 
    Returns
    -------------
    nuclei_object
        inferred nuclei
    nap
    """
    nuc_ch = NUC_CH
    median_size = 4   
    gauss_sigma = 1.34
    thresh_factor = 0.9
    thresh_min = 0.1
    thresh_max = 1.0
    min_hole_width = 0
    max_hole_width = 25
    small_obj_width = 15
    fill_filter_method = '3D'

    return infer_nuclei_fromlabel( in_img,
                                    nuc_ch,
                                    median_size,
                                    gauss_sigma,
                                    thresh_factor,
                                    thresh_min,
                                    thresh_max,
                                    min_hole_width,
                                    max_hole_width,
                                    small_obj_width,
                                    fill_filter_method)


##########################
#  infer_nuclei_fromcytoplasm
##########################
def infer_nuclei_fromcytoplasm(cytoplasm_mask: np.ndarray, 
                               nuc_min_width: int,
                               nuc_max_width: int,
                               fill_filter_method: str,
                               small_obj_width: int
                               ) -> np.ndarray:
    """
    Procedure to infer nuclei from linear unmixed input.

    Parameters
    ------------
    cytoplasm_mask: np.ndarray
        a 3d image of the cytoplasm segmentation
    max_hole_w: int
        hole filling cutoff to fill the nuclei
    small_obj_w: int
        object size cutoff to remove artifacts from dilation/erosion steps
    fill_filter_method: str
        to filter artifacts in "3D" or "slice-by-slice"

    Returns
    -------------
    nuclei_object
        mask defined extent of NU
    
    """

    ###################
    # PRE_PROCESSING
    ###################                
    cytoplasm_dilated = binary_dilation(cytoplasm_mask)

    cytoplasm_filled = fill_and_filter_linear_size(cytoplasm_dilated, 
                                                   hole_min=nuc_min_width, 
                                                   hole_max=nuc_max_width, 
                                                   min_size=0, 
                                                   method=fill_filter_method)

    cytoplasm_eroded = binary_erosion(cytoplasm_filled)

    ###################
    # CORE_PROCESSING
    ###################
    nuclei_xor = np.logical_xor(cytoplasm_mask, cytoplasm_eroded)

    ###################
    # POST_PROCESSING
    ###################
    nuclei_object = fill_and_filter_linear_size(nuclei_xor, 
                                                hole_min=0, 
                                                hole_max=0, 
                                                min_size=small_obj_width,
                                                method=fill_filter_method)

    nuclei_labels = label_uint16(nuclei_object)

    return nuclei_labels


##########################
#  fixed_infer_nuclei_fromcytoplasm
##########################
def fixed_infer_nuclei_fromcytoplasm(cytoplasm_mask: np.ndarray) -> np.ndarray:
    """
    Procedure to infer cellmask from linearly unmixed input, with a *fixed* set of parameters for each step in the procedure.  i.e. "hard coded"

    Parameters
    ------------
    in_img: np.ndarray
        a 3d image containing cytoplasm segmentation
 
    Returns
    -------------
    nuclei_object
        inferred nuclei
    
    """
    nuc_min_hole_w = 0
    nuc_max_hole_w = 500
    fill_filter_method = "3D"
    small_obj_w = 20

    return infer_nuclei_fromcytoplasm(cytoplasm_mask,
                                    nuc_min_hole_w,
                                    nuc_max_hole_w,
                                    fill_filter_method,
                                    small_obj_w)



def infer_and_export_nuclei(in_img: np.ndarray, meta_dict: Dict, out_data_path: Path) -> np.ndarray:
    """
    infer nuclei and write inferred nuclei to ome.tif file

    Parameters
    ------------
    in_img:
        a 3d  np.ndarray image of the inferred organelle (labels or boolean)
    meta_dict:
        dictionary of meta-data (ome)
    out_data_path:
        Path object where tiffs are written to

    Returns
    -------------
    exported file name

    """
    nuclei = fixed_infer_nuclei_fromlabel(in_img)

    out_file_n = export_inferred_organelle(nuclei, "nuclei", meta_dict, out_data_path)
    print(f"inferred nuclei. wrote {out_file_n}")
    return nuclei


def get_nuclei(in_img: np.ndarray, meta_dict: Dict, out_data_path: Path) -> np.ndarray:
    """
    load nucleus if it exists, otherwise calculate and write to ome.tif file

    Parameters
    ------------
    in_img:
        a 3d  np.ndarray image of the inferred organelle (labels or boolean)

    meta_dict:
        dictionary of meta-data (ome)
    out_data_path:
        Path object where tiffs are written to

    Returns
    -------------
    exported file name

    """

    try:
        nuclei = import_inferred_organelle("nuclei", meta_dict, out_data_path)
    except:
        start = time.time()
        print("starting segmentation...")
        nuclei = infer_and_export_nuclei(in_img, meta_dict, out_data_path)
        end = time.time()
        print(f"inferred nuclei in ({(end - start):0.2f}) sec")

    return nuclei


def get_nucleus(in_img: np.ndarray, meta_dict: Dict, out_data_path: Path) -> np.ndarray:
    """
    load nucleus if it exists, otherwise calculate and write to ome.tif file

    Parameters
    ------------
    in_img:
        a 3d  np.ndarray image of the inferred organelle (labels or boolean)

    meta_dict:
        dictionary of meta-data (ome)
    out_data_path:
        Path object where tiffs are written to

    Returns
    -------------
    exported file name

    """

    try:
        nucleus = import_inferred_organelle("nuc", meta_dict, out_data_path)
    except:
        start = time.time()
        print("starting segmentation...")
        nucleus = infer_and_export_nuclei(in_img, meta_dict, out_data_path)
        end = time.time()
        print(f"inferred nucleus in ({(end - start):0.2f}) sec")

    return nucleus

# def infer_nuclei_fromlabel_AICS(in_img: np.ndarray, meta_dict: Dict, out_data_path: Path) -> np.ndarray:
#     """
#     load nucleus if it exists, otherwise calculate and write to ome.tif file

#     Parameters
#     ------------
#     in_img:
#         a 3d  np.ndarray image of the inferred organelle (labels or boolean)

#     meta_dict:
#         dictionary of meta-data (ome)
#     out_data_path:
#         Path object where tiffs are written to

#     Returns
#     -------------
#     exported file name

#     """

#     try:
#         nuclei = import_inferred_organelle_AICS("nuclei", meta_dict, out_data_path)
#     except:
#         start = time.time()
#         print("starting nuclei segmentation...")
#         nuclei = fixed_infer_nuclei(in_img)
#         out_file_n = export_inferred_organelle_AICS(nuclei, "nuclei", meta_dict, out_data_path)
#         end = time.time()
#         print(f"inferred and saved nuclei AICS in ({(end - start):0.2f}) sec")

#     return nuclei
