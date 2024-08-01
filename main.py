import os
from modules import utility, displacement, stress, damage
from scripts import obtain_max_min

def main():
    # Load configuration
    print("++ Loading Configuration")
    config_dir =  os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = utility.load_config(config_dir)
    
    # Load data_input
    print("++ Loading Data Input")
    input_file_dir = "data/input/"
    input_dir =  os.path.join(os.path.dirname(__file__), input_file_dir, 'input_data.json')
    input_data = utility.load_json(input_dir)
    
    # Initiate twin from twin file
    print("++ Initializing the Twin")
    twin_file = utility.twin_file_handler(input_data, config) 
    twin_file_dir = config_dir =  os.path.join(os.path.dirname(__file__), twin_file)
    twin_model, tbrom_names = utility.initiate_twin(input_data, twin_file_dir)
    rom_index = input_data['input_parameters']['rom_index']
    rom_name = tbrom_names[rom_index]
    
    # Load the rst file and extract the mesh
    print("++ Reading the FEA mesh")
    rst_file = input_data['input_files']['rst_file']
    rst_file_dir =  os.path.join(os.path.dirname(__file__), rst_file)
    mesh, grid, mesh_unit = utility.extract_mesh(rst_file_dir)

    
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
    
    # Export to output_data.json
    print("++ Exporting to output_data.json")
    output_data_dir = 'data/output/'
    output_path = utility.export_output_data_to_json(twin_outputs, max_min_result, output_data_dir)
    print(f"DataFrames have been exported to {output_path}")
    
    # Export to result_field.json
    print("++ Exporting to result_field.json")
    result_field_dir = 'data/output/'
    result_field_path = os.path.join(result_field_dir, 'output.json')
    # Export DataFrame to JSON
    result_data.to_json(result_field_path, orient='records', lines=True)
    print(f"DataFrames have been exported to {result_field_path}")
    
if __name__ == "__main__":
    main()

