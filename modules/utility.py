from pytwin import TwinModel, TwinRuntime
import ansys.dpf.core as dpf
import yaml
import os
import json
# from pydpf import Model  # Example import, adjust as needed for PyDPF/PyTwin

def load_config(config_path):
    # Load the configuration file
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def initiate_twin(twin_file, rom_parameters=None, rom_inputs=None, field_inputs=None, json_config=None):
    # Implement logic to initiate twin from twin file
    twin_model = TwinModel(twin_file)
    try:
        twin_model.initialize_evaluation(parameters=rom_parameters, inputs=rom_inputs, field_inputs=field_inputs, json_config_filepath=json_config)
        tbrom_names = twin_model.tbrom_names
        print("+++ Twin Initialization Successful")
    except Exception as e:
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

def named_selections(twin_model, rom_name, mesh, named_selection=None):
    # Checking available named selections from twin
    named_selections_twin = twin_model.get_named_selections(rom_name)
    scoping_twin = named_selections_twin[0]
    
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
    
    # Mapping mesh from scoping
    mesh_scoping = dpf.operators.mesh.from_scoping(
        scoping=named_selections_fea[scoping_fea_index],
        nodes_only=False,
        mesh=mesh
    )
    # Get scoped mesh
    mesh = mesh_scoping.outputs.mesh()
    
    return scoping_twin_index, scoping_fea_index, mesh

def extract_output_parameters(twin, rst_file):
    # Example logic to extract parameters using PyDPF/PyTwin
    model = Model(rst_file)
    unit = model.metadata.result_info.unit  # Example to get unit, adjust as needed
    named_selections = model.metadata.named_selections  # Example to get named selections, adjust as needed
    return {
        'unit': unit,
        'named_selections': named_selections
    }

def export_results(result_data, output_dir, result_type, output_parameters):
    result_dir = os.path.join(output_dir, result_type)
    os.makedirs(result_dir, exist_ok=True)
    result_file = os.path.join(result_dir, 'results.json')
    with open(result_file, 'w') as file:
        json.dump(result_data, file)
    # Additional logic to handle output_parameters if needed
    if output_parameters.get('export_max_min'):
        max_min_file = os.path.join(result_dir, 'max_min.json')
        with open(max_min_file, 'w') as file:
            json.dump({"max": max(result_data), "min": min(result_data)}, file)

