#!/bin/bash
# Linux/Mac shell script to run the EMS to PowerFactory Converter
# 
# Usage: ./run_converter.sh [input_file] [output_directory]
# 
# Examples:
#   ./run_converter.sh my_ems_file.txt
#   ./run_converter.sh my_ems_file.txt output_folder
#   ./run_converter.sh my_ems_file.txt output_folder --verbose

echo "========================================"
echo "EMS to PowerFactory Converter"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH!"
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import pandas" &> /dev/null; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install required packages!"
        exit 1
    fi
fi

# Set default values
INPUT_FILE="$1"
OUTPUT_DIR="$2"
VERBOSE="$3"

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "ERROR: Please provide an input file!"
    echo
    echo "Usage: $0 [input_file] [output_directory]"
    echo "Example: $0 my_ems_file.txt output_folder"
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file '$INPUT_FILE' does not exist!"
    exit 1
fi

# Set default output directory if not provided
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="output"
fi

# Build the command
COMMAND="python3 ems_to_powerfactory_converter.py \"$INPUT_FILE\" -o \"$OUTPUT_DIR\""

# Add verbose flag if provided
if [ "$VERBOSE" == "--verbose" ]; then
    COMMAND="$COMMAND --verbose"
fi

echo
echo "Running converter with command:"
echo "$COMMAND"
echo

# Run the converter
eval $COMMAND

# Check if conversion was successful
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Conversion failed!"
    exit 1
fi

echo
echo "========================================"
echo "Conversion completed successfully!"
echo "========================================"
echo
echo "Output files are located in: $OUTPUT_DIR"
echo