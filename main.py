import os
from modules import utility, displacement, stress, damage, deflect_mesh
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
    
    # Validate input parameters
    try:
        utility.validate_parameters(input_data, config)
    except ValueError as e:
        print(e)
        exit(1)  # Stop the script with a non-zero exit code
    
    # Initiate twin from twin file
    print("++ Initializing the Twin")
    twin_file = utility.twin_file_handler(input_data, config) 
    twin_file_dir = os.path.join(os.path.dirname(__file__), twin_file)
    twin_model, tbrom_names = utility.initiate_twin(input_data, twin_file_dir)
    rom_index = input_data['input_parameters']['rom_index']
    rom_name = tbrom_names[rom_index]
    twin_outputs = twin_model.outputs
    
    # Load the rst file and extract the mesh
    print("++ Reading the FEA mesh")
    rst_file = input_data['input_files']['rst_file']
    rst_file_dir =  os.path.join(os.path.dirname(__file__), rst_file)
    mesh, grid, mesh_unit = utility.extract_mesh(rst_file_dir)

    
    # Obtain named selection scoping mesh 
    print("++ Obtaining named selections")
    
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
    result_unit = utility.get_unit(input_data, config)
    
    # Perform operations based on config
    operation, result_type = input_data["input_parameters"]["operation"]
    outfields, points = utility.get_result(twin_model, rom_name, scoping_twin=scoping_twin)
    if operation == 'displacement':
        result_data = displacement.get_result(input_data, outfields, points)
    elif operation == 'stress':
        result_data = stress.get_result(input_data, outfields, points)
    elif operation == 'fatigue':
        sn_curve_file_path = input_data['input_files']['sn_curve_file']
        result_data = damage.get_result(input_data, outfields, points, sn_curve_file_path)
    else:
        raise ValueError(f"Invalid operation: {operation}")
    
    # Projection result on mesh
    print("++ Projecting result on mesh")
    result_detail = "_".join(input_data["input_parameters"]["operation"])
    result_mesh, result_load_val = utility.project_result_on_mesh(result_data, grid, result_detail)


    # Deflect mesh from displacement result
    print("++ Deflecting mesh")
    main_dir = os.path.dirname(__file__)
    def_result_load_val = deflect_mesh.get_disp_result(input_data, main_dir)
    max_distance, max_magnitude, scale_factor = deflect_mesh.deflection_scale(config, result_mesh.points, def_result_load_val)
    print(" scale factor: ", scale_factor)
    print(" max distance: ", max_distance)
    print(" max magnitude: ", max_magnitude)
    
    # Plot result
    print("++ Plotting result")
    show_edges = input_data["output_files"]["3d_file"]["show_edges"]
    utility.plot_result(result_mesh, show_edges)

    # Export to 3d format
    print("++ Exporting result")
    output_3d_dir = os.path.join(os.path.dirname(__file__), input_data["output_files"]["3d_file"]["output_3d_dir"])
    utility.export_to_3d_file(result_mesh, output_3d_dir, input_data)

    # Obtaining max and min value
    print("++ Obtaining max and min value")
    max_result = obtain_max_min.obtain_max(result_data)
    min_result = obtain_max_min.obtain_min(result_data)
    max_min_result = {f"max {result_detail}": max_result, f"min {result_detail}": min_result}
    
    # Export to output_data.jsonW
    print("++ Exporting to output_data.json")
    output_data_path = os.path.join(os.path.dirname(__file__), input_data["output_files"]["output_dir"], input_data["output_files"]["data_file"]["output_data"])
    output_path = utility.export_output_data_to_json(output_data_path, result_unit, named_selection, twin_outputs=twin_outputs, output_parameters=max_min_result)
    print(f"DataFrames have been exported to {output_path}")
    
    # Export to result_field.json
    print("++ Exporting to result_field.json")
    output_dir = input_data["output_files"]["output_dir"]
    field_data_name =  result_detail +"_"+ input_data["output_files"]["data_file"]["field_data"]
    result_field_path = os.path.join(os.path.dirname(__file__), output_dir, field_data_name)
   
    # Export DataFrame to JSON
    result_data.to_json(result_field_path, orient='records', lines=True)
    print(f"DataFrames have been exported to {result_field_path}")
    
if __name__ == "__main__":
    main()

