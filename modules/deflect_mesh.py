from . import utility, displacement
import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

def get_disp_result(input_data, main_dir):   
    # Initiate twin from twin file
    twin_file = input_data["input_files"]["twin_file"]["displacement"]
    twin_file_dir = os.path.join(main_dir, twin_file)
    twin_model, tbrom_names = utility.initiate_twin(input_data, twin_file_dir)
    rom_index = input_data['input_parameters']['rom_index']
    rom_name = tbrom_names[rom_index]
    
    # Load the rst file and extract the mesh
    rst_file = input_data['input_files']['rst_file']
    rst_file_dir =  os.path.join(main_dir, rst_file)
    mesh, grid, mesh_unit = utility.extract_mesh(rst_file_dir)

    
    # Obtain named selection scoping mesh 
    named_selections_twin, named_selections_fea = utility.named_selections(twin_model, rom_name, mesh)
    
    named_selection = input_data['input_parameters']['named_selection']
    if named_selection == "All_Body":
        scoping = None
        nstwin, nsfea, mesh = utility.scoping(named_selections_twin, named_selections_fea, mesh, scoping=scoping)
        scoping_twin = None
        scoping_fea = None
    else: 
        scoping = input_data['input_parameters']['named_selection']
        nstwin, nsfea, mesh = utility.scoping(named_selections_twin, named_selections_fea, mesh, scoping=scoping)
        scoping_twin = named_selections_twin[nstwin]
        scoping_fea = named_selections_fea[nsfea]

    grid.points = utility.convert_to_meters(grid.points, mesh_unit)    
    
    # Perform operations based on config
    outfields, points = utility.get_result(twin_model, rom_name, scoping_twin=scoping_twin)
    if input_data["input_parameters"]["operation"][0] == "displacement":
        result_data = displacement.get_result(input_data, outfields, points)
    else:
        loc_xyz = utility.unflatten_vector(points, 3)
        base_data = {
            "x": loc_xyz[:, 0],
            "y": loc_xyz[:, 1],
            "z": loc_xyz[:, 2],
        }   
        norm = np.linalg.norm(outfields, axis=1)
        base_data["disp"] = norm
        result_data = pd.DataFrame(base_data)

    # Projection result on mesh
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    result_mesh, result_load_val = utility.project_result_on_mesh(result_data, grid, result_detail)
    return result_load_val

def deflection_scale(config, points, result_field):
    # Calculates the longest distance between any two points in a given array
    distances = cdist(points, points)
    max_distance = np.max(distances)

    # Find highes displacement
    max_magnitude = np.max(result_field)
    result_unit = config["operation_units"]["displacement"]
    max_magnitude = utility.convert_to_meters(max_magnitude, result_unit)

    # Calculate scale factor
    percent_def = config["autoscale"]
    scale_factor = (percent_def/100)*(max_distance/max_magnitude)
    return max_distance,max_magnitude, scale_factor


def get_deflected_mesh(mesh, config, points, outfields):
    # Deflect mesh from displacement result
    scale_factor = deflection_scale(config, points, outfields)
    scaled_disp = outfields * scale_factor
    mesh.grid.points = mesh.grid.points + scaled_disp*10
    return mesh    