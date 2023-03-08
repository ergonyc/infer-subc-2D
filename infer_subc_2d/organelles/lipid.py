import numpy as np

from infer_subc_2d.utils.img import (
    apply_threshold,
    scale_and_smooth,
    fill_and_filter_linear_size,
    select_channel_from_raw,
)
from infer_subc_2d.constants import LIPID_CH


##########################
#  infer_lipid
##########################
def infer_lipid(
                            in_img: np.ndarray,
                            median_sz: int,
                            gauss_sig: float,
                            method: str,
                            thresh_factor: float,
                            thresh_min: float,
                            thresh_max: float,
                            max_hole_w: int,
                            small_obj_w: int,
                        ) -> np.ndarray:
    """
    Procedure to infer peroxisome from linearly unmixed input.

    Parameters
    ------------
    in_img: 
        a 3d image containing all the channels
    median_sz: 
        width of median filter for signal
    gauss_sig: 
        sigma for gaussian smoothing of  signal
    method: 
        method for applying threshold.  "otsu"  or "li", "triangle", "median", "ave", "sauvola","multi_otsu","muiltiotsu"
    thresh_factor:
        scaling value for threshold
    thresh_min:
        absolute minumum for threshold
    thresh_max:
        absolute maximum for threshold
    max_hole_w: 
        hole filling cutoff for lipid post-processing
    small_obj_w: 
        minimu object size cutoff for lipid post-processing
    Returns
    -------------
    peroxi_object
        mask defined extent of peroxisome object
    """
    lipid_ch = LIPID_CH
    ###################
    # EXTRACT
    ###################    
    lipid = select_channel_from_raw(in_img, lipid_ch)
    ###################
    # PRE_PROCESSING
    ###################                         
    lipid =  scale_and_smooth(lipid,
                                                    median_sz = median_sz, 
                                                    gauss_sig = gauss_sig)


    ###################
    # CORE_PROCESSING
    ###################
    bw = apply_threshold(lipid, 
                                            method= method, 
                                            thresh_factor=thresh_factor, 
                                            thresh_min=thresh_min, 
                                            thresh_max=thresh_max)


    ###################
    # POST_PROCESSING
    ###################
    # min_hole_w = 0
    struct_obj = fill_and_filter_linear_size(bw, hole_min=0, hole_max=max_hole_w, min_size= small_obj_w)

    return struct_obj


##########################
#  fixed_infer_lipid
##########################
def fixed_infer_lipid(in_img: np.ndarray) -> np.ndarray:
    """
    Procedure to infer soma from linearly unmixed input, with a *fixed* set of parameters for each step in the procedure.  i.e. "hard coded"

    Parameters
    ------------
    in_img: 
        a 3d image containing all the channels

    Returns
    -------------
    lipid_body_object
        mask defined extent of liipid body

    """

    median_sz = 2   
    gauss_sig = 1.34
    method = "otsu"
    threshold_factor = 0.99 #from cellProfiler
    thresh_min = .5
    thresh_max = 1.
    max_hole_w = 2.5
    small_obj_w = 4

    return infer_lipid(
        in_img,  median_sz, gauss_sig, method, threshold_factor, thresh_min, thresh_max, max_hole_w, small_obj_w
    )
