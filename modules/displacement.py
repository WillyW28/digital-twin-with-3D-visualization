from . import utility
import numpy as np
import pandas as pd

def get_result(input_data, outfield, points):
    # Get displacement result
    results = utility.unflatten_vector(outfield, 3)
    loc_xyz = utility.unflatten_vector(points, 3)
 
    base_data = {
            "x": loc_xyz[:, 0],
            "y": loc_xyz[:, 1],
            "z": loc_xyz[:, 2],
    }
    result_type = input_data["input_parameters"]["operation"][1]
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    
    if result_type == "ux":
        base_data[result_detail] = results[:, 0]
    elif result_type == "uy":
        base_data[result_detail] = results[:, 1]
    elif result_type == "uz":
        base_data[result_detail] = results[:, 2]
    elif result_type == "norm":
        norm = np.linalg.norm(outfield, axis=1)
        base_data[result_detail] = norm
    else:
        raise ValueError("Invalid result_type")    
    
    
    return pd.DataFrame(base_data)

