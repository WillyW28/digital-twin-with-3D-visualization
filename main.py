import ansys.dpf.core as dpf

import pyvista as pv
import os
import numpy as np
import pandas as pd
import json
from modules import utility

def main():
    # Load configuration
    config_dir =  os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = utility.load_config(config_dir)
    
    # Collect ROM input data and file directories
    input_data = config['initial_value'][0]
    
    # Initiate twin from twin file
    twin_file = os.path.join(os.path.dirname(__file__), config['twin_file'])
    print("twin_file: ",twin_file)
    tbrom_names = utility.initiate_twin(twin_file=twin_file, rom_inputs=input_data)
    rom_name = tbrom_names[0]

    

if __name__ == "__main__":
    main()

