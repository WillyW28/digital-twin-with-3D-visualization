from pytwin import TwinModel
import yaml
import os
import json
# from pydpf import Model  # Example import, adjust as needed for PyDPF/PyTwin

def load_config(config_path):
    # Load the configuration file
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

# def collect_input_data(input_dir):
#     # Implement logic to collect input data
#     pass

# def setup_rom_input(input_data, input_parameters):
#     # Example of using nested parameters
#     param1_value = input_parameters['parameter1']['value']
#     param1_unit = input_parameters['parameter1']['unit']
#     param2_value = input_parameters['parameter2']['value']
#     param2_unit = input_parameters['parameter2']['unit']
#     named_selection = input_parameters['named_selection']

#     # Implement logic to set up ROM input using these parameters
#     pass

def initiate_twin(twin_file, rom_parameters=None, rom_inputs=None, field_inputs=None, json_config=None):
    # Implement logic to initiate twin from twin file
    twin_model = TwinModel(twin_file)
    try:
        twin_model.initialize_evaluation(parameters=rom_parameters, inputs=rom_inputs, field_inputs=field_inputs, json_config_filepath=json_config)
        tbrom_names = twin_model.tbrom_names
        print("++ Twin Initialization Successful")
    except Exception as e:
        tbrom_names = None
        print(f"Error initiating twin: {e}")
    return tbrom_names

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

