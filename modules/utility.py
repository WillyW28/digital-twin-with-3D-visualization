from pytwin import TwinModel
import ansys.dpf.core as dpf
import pyvista as pv
import yaml
import os
import numpy as np
import json
from scipy.spatial.distance import cdist

# from pydpf import Model  # Example import, adjust as needed for PyDPF/PyTwin

def load_config(config_path):
    # Load the configuration file
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
    
def load_json(json_path):
    # Load json file
    with open(json_path, 'r') as file:
        return json.load(file)

def validate_parameters(json_data, yaml_config):
    input_params = json_data['input_parameters']
    
    rom_index = input_params['rom_index']
    if rom_index not in yaml_config['available_roms']:
        raise ValueError(f"Error: ROM index '{rom_index}' is not valid. Available ROMs: {yaml_config['available_roms']}")
    
    # Validate 'named_selection'
    named_selection = input_params['named_selection']
    if named_selection not in yaml_config['availabe_named_selections']:
        raise ValueError(f"Error: Named selection '{named_selection}' is not valid. Available named selections: {yaml_config['availabe_named_selections']}")
    
    # Validate 'operation'
    operation = input_params['operation']
    if len(operation) != 2:
        raise ValueError(f"Error: Operation '{operation}' should have two parts.")
    
    parent_operation, child_operation = operation
    valid_operation = False
    for op_dict in yaml_config['available_operations']:
        if parent_operation in op_dict and child_operation in op_dict[parent_operation]:
            valid_operation = True
            break
    
    if not valid_operation:
        raise ValueError(f"Error: Operation '{parent_operation}_{child_operation}' is not valid. Available operations: {yaml_config['available_operations']}")
    
    # Validate 'deformation_scale'
    deformation_scale = input_params['deformation_scale']
    if deformation_scale not in yaml_config['available_deformation_scale']:
        raise ValueError(f"Error: Deformation scale '{deformation_scale}' is not valid. Available deformation scale: {yaml_config['available_deformation_scale']}")
    
    print("-- All input parameters are valid.")
    return True

def twin_file_handler(input_data, config):
    # Implement logic to handle input file
    operation = input_data['input_parameters']['operation'][0]
    
    # Extract the keys from available_operations
    available_operations = []
    for item in config['available_operations']:
        available_operations.extend(list(item.keys()))
        
    # Determine the correct twin file key based on the operation
    twin_file_key = 'stress' if operation == 'fatigue' else operation
    
    if twin_file_key in available_operations:
        twin_file = input_data['input_files']['twin_file'][twin_file_key]
    else:
        twin_file = None
        print(f"Invalid operation: {operation}. Available operations: {available_operations}")
    return twin_file

    
def initiate_twin(input_data, twin_file):
    # Initialize other parameters to None
    rom_parameters = None
    rom_inputs = None
    field_inputs = None

    # Extract potential inputs if they exist
    twin_inputs = input_data.get('twin_inputs', {})
    
    if 'rom_parameters' in twin_inputs:
        rom_parameters = twin_inputs['rom_parameters']
    
    if 'rom_inputs' in twin_inputs:
        rom_inputs = twin_inputs['rom_inputs']
    
    if 'field_inputs' in twin_inputs:
        field_inputs = twin_inputs['field_inputs']
        
    if 'json_config' in twin_inputs:
        json_config = twin_inputs['json_config']
        
    # Implement logic to initiate twin from twin file
    twin_model = TwinModel(twin_file)
    try:
        twin_model.initialize_evaluation(parameters=rom_parameters, inputs=rom_inputs, field_inputs=field_inputs, json_config_filepath=None)
        tbrom_names = twin_model.tbrom_names
        print("-- Twin Initialization Successful")
    except Exception as e:
        twin_model = None
        tbrom_names = None
        print(f"Error initiating twin: {e}")
    return twin_model, tbrom_names

def extract_mesh(rst_file):  
    
    # Load the Mechanical rst file through PyDPF and extract the mesh
    ds = dpf.DataSources()
    ds.set_result_file_path(rst_file)
    streams = dpf.operators.metadata.streams_provider(data_sources=ds)
    
    # Extracting the grid associated to the fea model
    mesh = dpf.operators.mesh.mesh_provider(streams_container=streams).eval()
    grid = mesh.grid
    mesh_unit = mesh.unit
    return mesh, grid, mesh_unit

def convert_to_meters(grid_coord, mesh_unit):
  # Conversion factors
    conversion_factors = {'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000}

    if mesh_unit == 'mm':
        grid_coord = grid_coord * conversion_factors['mm']
    elif mesh_unit == 'cm':
        grid_coord = grid_coord * conversion_factors['cm']
    elif mesh_unit == 'm':
        grid_coord = grid_coord * conversion_factors['m']
    elif mesh_unit == 'km':
        grid_coord = grid_coord * conversion_factors['km']
      
    return grid_coord

def named_selections(twin_model, rom_name, mesh):
    # Checking available named selections from twin
    named_selections_twin = twin_model.get_named_selections(rom_name)
    
    # Checking available named selections from fea
    named_selections_fea = mesh.available_named_selections
    return named_selections_twin, named_selections_fea

def scoping(named_selections_twin, named_selections_fea, mesh, scoping=None):
    # Convert the named selections to lowercase for case-insensitive matching
    named_selections_twin_lower = [name.lower() for name in named_selections_twin]
    named_selections_fea_lower = [name.lower() for name in named_selections_fea]
    
    # Normalize the scoping value
    scoping_lower = scoping.lower() if scoping else None
    
    # Initialize indices
    scoping_twin_index = None
    scoping_fea_index = None
    
    if scoping_lower:
        # Find the index in named_selections_twin
        if scoping_lower in named_selections_twin_lower:
            scoping_twin_index = named_selections_twin_lower.index(scoping_lower)

        # Find the index in named_selections_fea
        if scoping_lower in named_selections_fea_lower:
            scoping_fea_index = named_selections_fea_lower.index(scoping_lower)
    
        scoping_fea = mesh.named_selection(named_selections_fea[scoping_fea_index])
        # Mapping mesh from scoping
        mesh_scoping = dpf.operators.mesh.from_scoping(
            scoping=scoping_fea ,
            nodes_only=False,
            mesh=mesh
        )
        # Get scoped mesh
        mesh = mesh_scoping.outputs.mesh()
    
    return scoping_twin_index, scoping_fea_index, mesh

def deflection_scale(percent_def, points, outfield):
    # Calculates the longest distance between any two points in a given array
    distances = cdist(points, points)
    max_distance = np.max(distances)

    # Find highes displacement
    magnitudes = np.linalg.norm(outfield, axis=1)
    max_magnitude = np.max(magnitudes)

    scale_factor = (percent_def/100)*(max_distance/max_magnitude)
    return scale_factor
    pass

def deflect_mesh(mesh, twin_file, rom_index, scoping_twin, percent_def, rom_parameters=None, rom_inputs=None, field_inputs=None, json_config=None):
    twin_model, tbrom_names = initiate_twin(twin_file, rom_parameters=None, rom_inputs=None, field_inputs=None, json_config=None)
    rom_name = tbrom_names[rom_index]

    outfield = twin_model.generate_snapshot(rom_name, on_disk=False, named_selection=scoping_twin)
    points = twin_model.generate_points(rom_name, on_disk=False, named_selection=scoping_twin)

    scale_factor = deflection_scale(percent_def, points, outfield)

    scaled_disp = outfield * 10
    mesh.grid.points = mesh.grid.points + scaled_disp*10
    
    return mesh
    pass

def get_result(twin_model, rom_name, scoping_twin=None):
    # Get result data and point coordinates
    outfield = twin_model.generate_snapshot(rom_name, on_disk=False, named_selection=scoping_twin)
    points = twin_model.generate_points(rom_name, on_disk=False, named_selection=scoping_twin)
    return outfield, points

def unflatten_vector(vector: np.ndarray, dimensionality: int):
    # Unflatten a vector to array with specified number of columns
    return vector.reshape(-1, dimensionality)

def project_result_on_mesh(result, grid, result_type):
    # Convert imported data into NumPy array
    result_data = result.values
    nd_result_data = result_data[:,:].astype(float) 
    
    # Convert imported data into PolyData format
    wrapped = pv.PolyData(nd_result_data[:, :3])  
    wrapped[result_type] = nd_result_data[:, 3]  

    # Map the imported data to MAPDL grid
    inter_grid = grid.interpolate(
    wrapped, sharpness=5, radius=0.0001, strategy="closest_point", progress_bar=True)  # Map the imported data to MAPDL grid
    
    result_load_val = pv.convert_array(
        pv.convert_array(inter_grid.active_scalars)
    )  # Save result interpolated to each node as a NumPy array
    return inter_grid, result_load_val

def plot_result (inter_grid, show_edges=True):
    inter_grid.plot(show_edges=show_edges)  # Plot the interpolated data on MAPDL grid

def export_to_3d_file(inter_grid, output_dir, input_data):
    # Get input parameters
    output_type = input_data["output_files"]["3d_file"]["output_format"]
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    show_edges = input_data["output_files"]["3d_file"]["show_edges"]
    
    # Export to 3D file
    plotter = pv.Plotter()
    plotter.add_mesh(inter_grid, show_edges=show_edges)
    
    output_file = os.path.join(output_dir, result_detail)
    
    if output_type == 'gltf':
        plotter.export_gltf(f"{output_file}.gltf")
    elif output_type == 'vrml':
        plotter.export_vrml(f"{output_file}.wrl")
    elif output_type == 'obj':
        plotter.export_obj(f"{output_file}.obj")
    else:
        raise ValueError("Invalid output type. Please provide 'gltf', 'vrml', or 'obj'.") 

def get_unit(input_data, config):
    operation_units = config["operation_units"]
    operation, sub_operation =  input_data["input_parameters"]["operation"]

    for op_dict in config['available_operations']:
        if operation in op_dict:
             # Check if the child operation exists within the parent operation
            if sub_operation in op_dict[operation]:
                # Find the corresponding unit
                for unit_dict in config['operation_units']:
                    if operation in unit_dict:
                        # Handle special case for fatigue
                        if operation == 'fatigue':
                            for sub_unit_dict in unit_dict[operation]:
                                if sub_operation in sub_unit_dict:
                                    return sub_unit_dict[sub_operation]
                        else:
                            return unit_dict[operation]
    return None    

def export_output_data_to_json(output_file, result_unit, named_selection, twin_outputs=None, output_parameters=None):
    # Structure the data in a dictionary
    data = {
        "twin_outputs": twin_outputs,
        "output_parameters": output_parameters,
        "unit": result_unit,
        "named_selection": named_selection
    }
    
    # Write the dictionary to a JSON file
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    return output_file
