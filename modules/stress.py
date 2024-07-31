from . import utility
import numpy as np
import pandas as pd

def calculate_von_mises(stress_array):
    von_mises_stresses = []
    
    for stress in stress_array:
        sigma_xx, sigma_yy, sigma_zz, sigma_xy, sigma_yz, sigma_zx = stress
        
        # Calculate von Mises stress
        von_mises = np.sqrt(
            0.5 * (
                (sigma_xx - sigma_yy) ** 2 +
                (sigma_yy - sigma_zz) ** 2 +
                (sigma_zz - sigma_xx) ** 2 +
                6 * (sigma_xy ** 2 + sigma_yz ** 2 + sigma_zx ** 2)
            )
        )
        
        von_mises_stresses.append(von_mises)
    
    return np.array(von_mises_stresses)
    
def get_result(outfield, points, result_type):
    # Get displacement result
    results = utility.unflatten_vector(outfield, 6)
    loc_xyz = utility.unflatten_vector(points, 3)

    base_data = {
            "x": loc_xyz[:, 0],
            "y": loc_xyz[:, 1],
            "z": loc_xyz[:, 2],
    }
    
    if result_type == "sx":
        base_data["result"] = results[:, 0]
    elif result_type == "sy":
        base_data["result"] = results[:, 1]
    elif result_type == "sz":
        base_data["result"] = results[:, 2]
    elif result_type == "sxx":
        base_data["result"] = results[:, 3]
    elif result_type == "syz":
        base_data["result"] = results[:, 4]
    elif result_type == "sxz":
        base_data["result"] = results[:, 5]
    elif result_type == "seqv":
        vm = calculate_von_mises(outfield)
        base_data["result"] = vm
    else:
        raise ValueError("Invalid result_type")    
    
    
    return pd.DataFrame(base_data), outfield

