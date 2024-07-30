import ansys.dpf.core as dpf

import pyvista as pv
import os
import numpy as np
import pandas as pd
import json
from modules import utility

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
    rom_name = tbrom_names[0]
    
    # Load the rst file and extract the mesh
    print("++ Reading the FEA mesh")
    rst_file = os.path.join(os.path.dirname(__file__), config['rst_file'])
    mesh, grid, mesh_unit = utility.extract_mesh(rst_file)
    grid.points = utility.convert_to_meters(grid.points, mesh_unit)    
    
if __name__ == "__main__":
    main()

