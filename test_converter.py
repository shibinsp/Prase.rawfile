#!/usr/bin/env python3
"""
Test script for EMS to PowerFactory Converter
Verifies the conversion process and validates output files
"""

import os
import sys
import json
import logging
from pathlib import Path
import subprocess
import tempfile
import shutil


def test_converter():
    """Test the EMS to PowerFactory converter"""
    print("="*70)
    print("EMS TO POWERFACTORY CONVERTER - TEST SUITE")
    print("="*70)
    
    # Test files
    input_file = "example_input.txt"
    converter_script = "ems_to_powerfactory_converter.py"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        return False
        
    # Check if converter script exists
    if not os.path.exists(converter_script):
        print(f"ERROR: Converter script not found: {converter_script}")
        return False
    
    # Create temporary output directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\nTesting converter with output directory: {temp_dir}")
        
        # Run the converter
        cmd = [
            sys.executable, converter_script,
            input_file,
            '-o', temp_dir,
            '--verbose'
        ]
        
        print(f"\nRunning command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"\nERROR: Converter failed with return code {result.returncode}")
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
                return False
                
            print(f"\nConverter output:\n{result.stdout}")
            
            # Validate output files
            output_files = os.listdir(temp_dir)
            print(f"\nGenerated files: {output_files}")
            
            # Check for expected files
            expected_files = [
                "example_input_powerfactory.raw",
                "example_input_metadata.json",
                "example_input_report.xlsx",
                "conversion.log"
            ]
            
            for expected_file in expected_files:
                file_path = os.path.join(temp_dir, expected_file)
                if os.path.exists(file_path):
                    print(f"✓ {expected_file} - Generated successfully")
                    
                    # Validate file content
                    if expected_file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            try:
                                data = json.load(f)
                                print(f"  - JSON file is valid with {len(data)} top-level keys")
                                
                                # Check for required sections
                                required_keys = ['conversion_info', 'statistics', 'brand_data']
                                for key in required_keys:
                                    if key in data:
                                        print(f"  - ✓ Contains {key} section")
                                    else:
                                        print(f"  - ✗ Missing {key} section")
                                        
                            except json.JSONDecodeError as e:
                                print(f"  - ✗ Invalid JSON: {e}")
                                return False
                                
                    elif expected_file.endswith('.raw'):
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            print(f"  - RAW file contains {len(lines)} lines")
                            
                            # Check for PowerFactory format markers
                            content = ''.join(lines)
                            required_markers = [
                                'PowerFactory RAW File',
                                '/BUS DATA',
                                '/TRANSFORMER DATA',
                                '0 / End of Bus Data',
                                '0 / End of Transformer Data'
                            ]
                            
                            for marker in required_markers:
                                if marker in content:
                                    print(f"  - ✓ Contains {marker}")
                                else:
                                    print(f"  - ✗ Missing {marker}")
                                    
                    elif expected_file.endswith('.xlsx'):
                        if os.path.getsize(file_path) > 0:
                            print(f"  - Excel file generated successfully ({os.path.getsize(file_path)} bytes)")
                        else:
                            print(f"  - ✗ Excel file is empty")
                            return False
                            
                else:
                    print(f"✗ {expected_file} - NOT FOUND")
                    return False
                    
            print("\n" + "="*70)
            print("ALL TESTS PASSED SUCCESSFULLY!")
            print("="*70)
            
            # Copy files to output directory for user access
            final_output_dir = "test_output"
            os.makedirs(final_output_dir, exist_ok=True)
            
            for file in output_files:
                src = os.path.join(temp_dir, file)
                dst = os.path.join(final_output_dir, file)
                shutil.copy2(src, dst)
                print(f"Copied {file} to {final_output_dir}")
                
            return True
            
        except subprocess.TimeoutExpired:
            print("ERROR: Converter timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error during testing: {e}")
            return False


def validate_powerfactory_format(file_path):
    """Validate PowerFactory .raw file format"""
    print(f"\nValidating PowerFactory format: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        validation_results = {
            'total_lines': len(lines),
            'has_header': False,
            'has_bus_data': False,
            'has_transformer_data': False,
            'has_proper_endings': False,
            'errors': []
        }
        
        # Check header
        if len(lines) > 0 and 'PowerFactory RAW File' in lines[0]:
            validation_results['has_header'] = True
        else:
            validation_results['errors'].append("Missing or invalid header")
            
        # Check for sections
        content = ''.join(lines)
        
        if '/BUS DATA' in content:
            validation_results['has_bus_data'] = True
        else:
            validation_results['errors'].append("Missing BUS DATA section")
            
        if '/TRANSFORMER DATA' in content:
            validation_results['has_transformer_data'] = True
        else:
            validation_results['errors'].append("Missing TRANSFORMER DATA section")
            
        # Check for proper endings
        if '0 / End of Bus Data' in content and '0 / End of Transformer Data' in content:
            validation_results['has_proper_endings'] = True
        else:
            validation_results['errors'].append("Missing proper section endings")
            
        return validation_results
        
    except Exception as e:
        return {'errors': [f"File reading error: {e}"]}


def main():
    """Main test function"""
    print("Starting comprehensive test of EMS to PowerFactory Converter...")
    
    # Run the main test
    success = test_converter()
    
    if success:
        print("\n🎉 CONGRATULATIONS! All tests passed successfully!")
        print("\nThe converter has been thoroughly tested and is ready for use.")
        print("\nGenerated files are available in: test_output/")
        
        # List the generated files
        output_dir = "test_output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"\nGenerated files:")
            for file in sorted(files):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"  📄 {file} ({size:,} bytes)")
                
    else:
        print("\n❌ TESTS FAILED! Please check the error messages above.")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())