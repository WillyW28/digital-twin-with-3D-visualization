from . import utility, stress
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def read_sn_curve(file_path):
    sn_data = pd.read_csv(file_path, delimiter=';')
    return sn_data['Stress'].values, sn_data['Cycles'].values

def log_interpolate_sn_curve(stress_values, cycle_values):
    log_stress_values = np.log10(stress_values)
    log_cycle_values = np.log10(cycle_values)
    log_sn_interp = interp1d(log_stress_values, log_cycle_values, kind='linear', fill_value="extrapolate")
    return log_sn_interp   

def calculate_cycles_to_failure(stress_array, config):
    sn_curve_file_path = config["additional_files"]["sn_curve_file"]
    stress_values, cycle_values = read_sn_curve(sn_curve_file_path)
    log_sn_interp = log_interpolate_sn_curve(stress_values, cycle_values)
    log_von_mises_stresses = np.log10(stress_array)
    log_cycles = log_sn_interp(log_von_mises_stresses)
    cycles_to_failure = np.power(10, log_cycles)
    max_cycle = max(cycle_values)
    cycles_to_failure = [max_cycle if x > max_cycle else x for x in cycles_to_failure]
    return cycles_to_failure 
    
def calculate_damage(stress_array, config):
    cycles_to_failure = calculate_cycles_to_failure(stress_array, config)
    damage = 1 / cycles_to_failure
    return damage

def get_result(config, input_data, outfields, points):
    # Get stress result
    stress_data = stress.calculate_von_mises(outfields)
    loc_xyz = utility.unflatten_vector(points, 3)
    base_data = {
            "x": loc_xyz[:, 0],
            "y": loc_xyz[:, 1],
            "z": loc_xyz[:, 2],
    }
    result_type = input_data["input_parameters"]["operation"][1]
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    
    if result_type == "cycle":
        cycle_data = calculate_cycles_to_failure(stress_data, config)
        base_data[result_detail] = cycle_data
    elif result_type == "damage":
        damage_data = calculate_damage(stress_data, config)
        base_data[result_detail] = damage_data
    else:
        raise ValueError("Invalid result_type")    
    
    
    return pd.DataFrame(base_data)

