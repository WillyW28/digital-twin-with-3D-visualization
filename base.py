import os
import yaml
import json
from modules import utility, displacement, stress, damage
from scripts import obtain_max_min
from fastapi import HTTPException

async def load_config(config_path):
    # Load configuration
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")

async def load_data(json_path):
    # Load data_input
    try :
        with open(json_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")
    

async def validate_input(input_data, config):
    # Validate input parameters
    try:
        utility.validate_parameters(input_data, config)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")
    
async def initialize_twin(input_data, config):
    # Initiate twin from twin file
    try:
        twin_file = utility.twin_file_handler(input_data, config) 
        twin_model, tbrom_names = utility.initiate_twin(input_data, twin_file)
        rom_index = input_data['input_parameters']['rom_index']
        rom_name = tbrom_names[rom_index]
        twin_outputs = twin_model.outputs
        return twin_model, rom_name, twin_outputs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inititalize twin: {str(e)}")

async def extract_mesh(input_data):
    # Load the rst file and extract the mesh
    try:
        rst_file = input_data['input_files']['rst_file']
        mesh, grid, mesh_unit = utility.extract_mesh(rst_file)
        grid.points = utility.convert_to_meters(grid.points, mesh_unit)  
        return mesh, grid, mesh_unit
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract mesh: {str(e)}")

async def get_named_selection(input_data, twin_model, rom_name, mesh):
    # Obtain named selection scoping mesh 
    try:
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
        return scoping_twin, scoping_fea
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get named selection: {str(e)}")
    
async def get_results(input_data, config, twin_model, rom_name, scoping_twin):
    # Get result based on operation
    try:
        # Get result unit
        result_unit = utility.get_unit(input_data, config)
        # Perform operations based on config
        operation = input_data["input_parameters"]["operation"][0]
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
        return result_data, result_unit
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")
    
async def project_results_on_mesh(input_data, result_data, grid):
    # Projection result on mesh
    try:
        result_detail = "_".join(input_data["input_parameters"]["operation"])
        result_mesh, result_load_val = utility.project_result_on_mesh(result_data, grid, result_detail)
        return result_mesh, result_load_val
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to project result on mesh: {str(e)}")
    
async def deflect_mesh(input_data, config, result_mesh):
    # Deflecting mesh from displacement result
    try:
        result_mesh = utility.deflect_mesh(input_data, config, result_mesh)
        return result_mesh
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deflect mesh: {str(e)}")

async def plot_results(input_data, result_mesh):
    # Plotting result
    try:
        show_edges = input_data["output_files"]["3d_file"]["show_edges"]
        utility.plot_result(result_mesh, show_edges)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to plot result: {str(e)}")

async def export_to_3d_format(input_data, result_mesh):
    # Exporting to 3d format
    try:    
        output_3d_dir = input_data["output_files"]["3d_file"]["output_3d_dir"]
        utility.export_to_3d_file(result_mesh, output_3d_dir, input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export to 3d format: {str(e)}")

async def obtain_maxmin(input_data, result_data):
    # Obtaining max and min value
    try: 
        max_result = obtain_max_min.obtain_max(result_data)
        min_result = obtain_max_min.obtain_min(result_data)
        result_detail = "_".join(input_data["input_parameters"]["operation"])
        max_min_result = {f"max {result_detail}": max_result, f"min {result_detail}": min_result}
        return max_min_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to obtain max and min value: {str(e)}")
   
async def export_output_to_json(input_data, result_unit, named_selection, twin_outputs, max_min_result):
    # Exporting to output_data.json
    try:
        output_data_path = os.path.join(input_data["output_files"]["output_dir"], input_data["output_files"]["data_file"]["output_data"])
        utility.export_output_data_to_json(output_data_path, result_unit, named_selection, twin_outputs=twin_outputs, output_parameters=max_min_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export output to json: {str(e)}")

async def export_field_to_json(input_data, result_data):
    # Export to result_field.json
    try:
        output_dir = input_data["output_files"]["output_dir"]
        result_detail = "_".join(input_data["input_parameters"]["operation"])
        field_data_name =  result_detail +"_"+ input_data["output_files"]["data_file"]["field_data"]
        result_field_path = os.path.join(output_dir, field_data_name)
        result_data.to_json(result_field_path, orient='records', lines=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export field to json: {str(e)}")
    
    
