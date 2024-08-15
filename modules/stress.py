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
    
def get_result(config, input_data, outfield, points):
    # Get displacement result
    results = utility.unflatten_vector(outfield, 6)
    loc_xyz = utility.unflatten_vector(points, 3)

    base_data = {
            "x": loc_xyz[:, 0],
            "y": loc_xyz[:, 1],
            "z": loc_xyz[:, 2],
    }
    
    result_type = input_data["input_parameters"]["operation"][1]
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    
    if result_type == "xx":
        base_data[result_detail] = results[:, 0]
    elif result_type == "yy":
        base_data[result_detail] = results[:, 1]
    elif result_type == "zz":
        base_data[result_detail] = results[:, 2]
    elif result_type == "xy":
        base_data[result_detail] = results[:, 3]
    elif result_type == "yz":
        base_data[result_detail] = results[:, 4]
    elif result_type == "xz":
        base_data[result_detail] = results[:, 5]
    elif result_type == "von_mises":
        vm = calculate_von_mises(outfield)
        base_data[result_detail] = vm
    else:
        raise ValueError("Invalid result_type")    
    
    
    return pd.DataFrame(base_data)

