# Digital Twin Project

## Overview

This project is a digital twin implementation using Ansys with PyAnsys (PyTwin and PyDPF). The digital twin can perform various analyses (stress, displacement, damage, etc.) and is designed to be scalable for any model in the future. The project is intended for future integration with IoT devices.

## Setup

### Prerequisites

- Python 3.7+
- Ansys License

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/WillyW28/digital-twin-with-3D-visualization.git
    cd project_name
    ```

2. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Edit the `config.yaml` file to configure the settings for different models and other configurations.

### Input Data

Edit the `data/input/input_data.json` file to configure the settings for different input setup.

## Usage

### Running the Digital Twin Script

To run the digital twin model analysis, execute:
```bash
python main.py
```

## Future Work
- Integrate with IoT devices using AWS IoT, Azure IoT Hub, or Google Cloud IoT.
- Expand the analysis capabilities to include more models.
- Enhance security and add authentication to the API.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any improvements or suggestions.

## License

This project is licensed under the MIT License. See the LICENSE file for details.