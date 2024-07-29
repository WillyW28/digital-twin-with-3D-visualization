import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

config = load_config('config.yaml')

# Accessing values from the config
input_dir = config['input_dir']
operations = config['operations']
print(f"Input Directory: {input_dir}")
print(f"Operations to perform: {operations}")