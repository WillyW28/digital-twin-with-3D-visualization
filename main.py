import os
from modules import utility, displacement, stress, damage
from scripts import obtain_max_min
import json

def main():
    # Load configuration
    print("++ Loading Configuration")
    config_dir =  os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = utility.load_config(config_dir)
    
    # Collect ROM input data 
    print("++ Collecting Input Data")
    input_data = config['initial_value'][0]
    
    # Initiate twin from twin file
    print("++ Initializing the Twin")
    twin_file = os.path.join(os.path.dirname(__file__), config['twin_file'])
    twin_model, tbrom_names = utility.initiate_twin(twin_file=twin_file, rom_inputs=input_data)
    rom_index = 0
    rom_name = tbrom_names[rom_index]
    
    # Load the rst file and extract the mesh
    print("++ Reading the FEA mesh")
    rst_file = os.path.join(os.path.dirname(__file__), config['rst_file'])
    mesh, grid, mesh_unit = utility.extract_mesh(rst_file)
    
    
    # Obtain named selection scoping mesh 
    print("++ Obtaining named selections")
    scoping = config['scoping']
    named_selections_twin, named_selections_fea = utility.named_selections(twin_model, rom_name , mesh, named_selection=scoping)
    nstwin, nsfea, mesh = utility.scoping(named_selections_twin, named_selections_fea, mesh, scoping=scoping)
    scoping_twin = named_selections_twin[nstwin]
    scoping_fea = named_selections_fea[nsfea]
    grid.points = utility.convert_to_meters(grid.points, mesh_unit)    
    
    # Deflect mesh from displacement result
    print("++ Deflecting mesh")
    pass
    
    # Perform operations based on config
    operation, result_type = config["operation"]
    outfields, points = utility.get_result(twin_model, rom_name, scoping_twin=scoping_twin)
    if operation == 'displacement':
        result_data = displacement.get_result(outfields, points, result_type)
    elif operation == 'stress':
        result_data = stress.get_result(outfields, points, result_type)
    elif operation == 'fatigue':
        sn_curve_file_path = 'data/raw/sn_curve.csv'
        result_data = damage.get_result(outfields, points, result_type, sn_curve_file_path)
    else:
        raise ValueError(f"Invalid operatioWn: {operation}")
    print(result_data)
    
    # Projection result on mesh
    print("++ Projecting result on mesh")
    result_detail = "_".join(config['operation'])
    result_mesh = utility.project_result_on_mesh(result_data, grid, result_detail)

    # Plot result
    print("++ Plotting result")
    show_edges = config['mesh_settings']['show_edges']
    utility.plot_result(result_mesh, show_edges)

    # Export to 3d format
    print("++ Exporting result")
    output_type = config['mesh_settings']['format']
    output_dir = os.path.join(os.path.dirname(__file__), config['output_dir'])
    utility.export_to_3d_file(result_mesh, output_type, result_detail, show_edges, output_dir)

    # Obtaining max and min value
    print("++ Obtaining max and min value")
    max_result = obtain_max_min.obtain_max(result_data)
    min_result = obtain_max_min.obtain_min(result_data)
    max_min_result = {"max": max_result, "min": min_result}
    output_data_dir = 'data/output/'
    output_file = 'output_data.json'
    
    os.makedirs(output_data_dir, exist_ok=True)
    output_path = os.path.join(output_data_dir, output_file)
    
    with open(output_path, 'w') as f:
    json.dump(max_min_result, f, indent=4)

    print(f"DataFrames have been exported to {output_path}")
    
    
if __name__ == "__main__":
    main()

