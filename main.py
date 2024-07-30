import ansys.dpf.core as dpf
from pytwin import TwinModel
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
    print(config)

if __name__ == "__main__":
    main()

