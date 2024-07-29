import ansys.dpf.core as dpf
from pytwin import TwinModel
import pyvista as pv
import os
import numpy as np
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

data_path = os.path.join(project_dir, 'data')
models_path = os.path.join(project_dir, 'models')
modules_path = os.path.join(project_dir, 'modules')

print(os.path.abspath(__file__))
print(script_dir)
print(project_dir)
print(os.path.dirname(project_dir))

