#!/usr/bin/env python3
"""
Demonstration script for EMS to PowerFactory Converter
Shows how to use the converter programmatically
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ems_to_powerfactory_converter import EMSToPowerFactoryConverter


def demo_basic_usage():
    """Demonstrate basic usage of the converter"""
    print("="*60)
    print("EMS TO POWERFACTORY CONVERTER - DEMONSTRATION")
    print("="*60)
    
    # Example 1: Basic conversion
    print("\n1. Basic Conversion Example:")
    print("-" * 40)
    
    input_file = "example_input.txt"  # Using the example input file
    output_dir = "output"
    
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    
    # Create converter instance
    converter = EMSToPowerFactoryConverter(input_file, output_dir)
    
    try:
        # Execute conversion
        results = converter.convert()
        
        print("\n✓ Conversion completed successfully!")
        print(f"  PowerFactory .raw file: {results['powerfactory_raw']}")
        print(f"  Metadata JSON file: {results['metadata_json']}")
        print(f"  Excel report: {results['excel_report']}")
        print(f"  Log file: {results['log_file']}")
        
        # Display system statistics
        stats = converter.metadata['statistics']
        print(f"\nSystem Summary:")
        print(f"  Total Buses: {stats['total_buses']}")
        print(f"  Total Transformers: {stats['total_transformers']}")
        print(f"  Total Generators: {stats['total_generators']}")
        print(f"  Total Loads: {stats['total_loads']}")
        print(f"  Total Branches: {stats['total_branches']}")
        
        if 'total_generation_capacity_mva' in stats:
            print(f"  Total Generation Capacity: {stats['total_generation_capacity_mva']:.2f} MVA")
        if 'total_load_demand_mw' in stats:
            print(f"  Total Load Demand: {stats['total_load_demand_mw']:.2f} MW")
        
        # Show voltage levels
        voltage_levels = stats.get('voltage_levels', [])
        print(f"  Voltage Levels: {sorted(voltage_levels)} kV")
        
    except Exception as e:
        print(f"\n✗ Error during conversion: {e}")
        return False
    
    return True


def demo_advanced_usage():
    """Demonstrate advanced usage with custom parameters"""
    print("\n\n2. Advanced Usage Example:")
    print("-" * 40)
    
    input_file = "your_ems_file.txt"  # Replace with your actual file
    output_dir = "demo_advanced_output"
    
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    
    # Create converter with custom settings
    converter = EMSToPowerFactoryConverter(input_file, output_dir)
    
    try:
        # Parse the file first
        converter.parse_ems_file()
        
        # Generate files with custom names
        raw_file = converter.generate_powerfactory_raw(f"{output_dir}/custom_powerfactory.raw")
        json_file = converter.generate_metadata_json(f"{output_dir}/system_metadata.json")
        excel_file = converter.generate_excel_report(f"{output_dir}/analysis_report.xlsx")
        
        print("\n✓ Advanced conversion completed!")
        print(f"  Custom PowerFactory file: {raw_file}")
        print(f"  Custom metadata file: {json_file}")
        print(f"  Custom Excel report: {excel_file}")
        
        # Access metadata directly
        metadata = converter.metadata
        print(f"\nDetailed System Information:")
        print(f"  Conversion Date: {metadata['conversion_info']['conversion_date']}")
        print(f"  Base Frequency: {metadata['conversion_info']['base_frequency']} Hz")
        print(f"  System Name: {metadata['conversion_info']['system_name']}")
        
        # Show brand data
        brand_data = metadata.get('brand_data', {})
        if brand_data.get('transformers'):
            print(f"  Transformer Brands: {len(brand_data['transformers'])} entries")
        if brand_data.get('generators'):
            print(f"  Generator Brands: {len(brand_data['generators'])} entries")
        
    except Exception as e:
        print(f"\n✗ Error during advanced conversion: {e}")
        return False
    
    return True


def demo_api_usage():
    """Demonstrate API usage for programmatic access"""
    print("\n\n3. API Usage Example:")
    print("-" * 40)
    
    input_file = "your_ems_file.txt"  # Replace with your actual file
    output_dir = "demo_api_output"
    
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Create converter instance
        converter = EMSToPowerFactoryConverter(input_file, output_dir)
        
        # Parse the EMS file
        converter.parse_ems_file()
        
        # Access data structures directly
        print(f"\nDirect Data Access:")
        print(f"  Number of buses: {len(converter.buses)}")
        print(f"  Number of transformers: {len(converter.transformers)}")
        print(f"  Number of generators: {len(converter.generators)}")
        print(f"  Number of loads: {len(converter.loads)}")
        print(f"  Number of branches: {len(converter.branches)}")
        
        # Example: Find all 110kV buses
        kv110_buses = [bus for bus in converter.buses.values() if abs(bus.base_kv - 110.0) < 1.0]
        print(f"  110kV buses: {len(kv110_buses)}")
        
        # Example: Find transformers by voltage ratio
        transformers_110_33 = [tx for tx in converter.transformers 
                              if tx.from_bus_voltage == 110.0 and tx.to_bus_voltage == 33.0]
        print(f"  110/33kV transformers: {len(transformers_110_33)}")
        
        # Example: Calculate total generation capacity
        total_gen_capacity = sum(gen.mva_base for gen in converter.generators)
        print(f"  Total generation capacity: {total_gen_capacity:.2f} MVA")
        
        # Generate output files
        results = converter.convert()
        print(f"\n✓ API usage completed successfully!")
        print(f"  Generated files in: {output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error during API usage: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main demonstration function"""
    print("EMS to PowerFactory Converter - Demonstration")
    print("This script demonstrates various usage patterns of the converter.")
    
    # Run demonstrations
    success1 = demo_basic_usage()
    success2 = demo_advanced_usage()
    success3 = demo_api_usage()
    
    print("\n" + "="*60)
    print("DEMONSTRATION SUMMARY")
    print("="*60)
    
    if success1 and success2 and success3:
        print("🎉 All demonstrations completed successfully!")
        print("\nThe converter is ready for production use.")
        print("\nKey Features Demonstrated:")
        print("  ✓ Basic file conversion")
        print("  ✓ Custom output file naming")
        print("  ✓ Programmatic API access")
        print("  ✓ Comprehensive error handling")
        print("  ✓ Detailed metadata extraction")
        print("  ✓ Excel report generation")
        print("  ✓ Brand data extraction")
        print("  ✓ System statistics calculation")
    else:
        print("❌ Some demonstrations failed. Please check the error messages above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())