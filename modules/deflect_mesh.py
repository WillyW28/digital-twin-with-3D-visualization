from . import utility, displacement
import os
import numpy as np
import pandas as pd
import pyvista as pv
from scipy.spatial.distance import cdist


def project_result_on_mesh(outfields, points, grid):
    # Project results onto the MAPDL grid
    
    # Convert imported data into PolyData format
    wrapped = pv.PolyData(points)  
    
    # Add the result data to the PolyData object
    wrapped["ux"] = outfields[:,0]
    wrapped["uy"] = outfields[:,1]
    wrapped["uz"] = outfields[:,2]

    # Map the imported data to MAPDL grid
    inter_grid = grid.interpolate(
    wrapped, sharpness=5, radius=0.0001, strategy="closest_point")  # Map the imported data to MAPDL grid
    
    # Extract interpolated results for ux, uy, uz
    interpolated_ux = inter_grid["ux"]
    interpolated_uy = inter_grid["uy"]
    interpolated_uz = inter_grid["uz"]
    
    # Combine interpolated results into a single array
    result_load_val = np.vstack((interpolated_ux, interpolated_uy, interpolated_uz)).T

    return inter_grid, result_load_val

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

    # Projection result on mesh
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    result_mesh, result_load_val = project_result_on_mesh(outfields, points, grid)
    return result_load_val, result_mesh

def deflection_scale(config, input_data, points, result_field):
    # Calculates the longest distance between any two points in a given array
    distances = cdist(points, points)
    max_distance = np.max(distances)

    # Find highes displacement
    if input_data["input_parameters"]["operation"][0] == "ux":
        disp = result_field[:,0]
    elif input_data["input_parameters"]["operation"][0] == "uy":
        disp = result_field[:,1]
    elif input_data["input_parameters"]["operation"][0] == "uz":
        disp = result_field[:,2]
    else:
        disp = np.linalg.norm(result_field, axis=1)
    max_magnitude = np.max(disp)
    result_unit = config["operation_units"]["displacement"]
    max_magnitude = utility.convert_to_meters(max_magnitude, result_unit)

    # Calculate scale factor
    percent_def = config["autoscale"]
    scale_factor = (percent_def/100)*(max_distance/max_magnitude)
    return scale_factor

def get_deflected_mesh(mesh, config, input_data, outfields, scale_parameter, scale_factor_ow):
    # Filter outfields
    filtered = np.zeros_like(outfields)
    result_type = input_data["input_parameters"]["operation"][1]
    if result_type == "ux":
        filtered[:, 0] = outfields[:, 0]
    elif result_type == "uy":
        filtered[:, 1] = outfields[:, 1]
    elif result_type == "uz":
        filtered[:, 2] = outfields[:, 2]
    else:        
        filtered = outfields

    # Deflect mesh from displacement result
    
    if scale_factor_ow == True:
        scale_factor = 1
    else: 
        scale_factor = deflection_scale(config, input_data, mesh.points, filtered) * scale_parameter
    filtered = utility.convert_to_meters(filtered, config["operation_units"]["displacement"])
    scaled_disp = filtered * scale_factor
    mesh.points = mesh.points + scaled_disp
    
    return mesh