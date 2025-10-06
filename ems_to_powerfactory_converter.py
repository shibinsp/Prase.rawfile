#!/usr/bin/env python3


import json
import logging
import argparse
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


@dataclass
class BusData:
    """Bus data structure for PowerFactory compatibility"""
    bus_number: int
    name: str
    base_kv: float
    bus_type: int
    voltage_magnitude: float
    voltage_angle: float
    area: int
    zone: int
    max_voltage: float
    min_voltage: float
    description: str = ""


@dataclass
class TransformerData:
    """Transformer data structure"""
    from_bus: int
    to_bus: int
    circuit_id: str
    winding_type: int
    control_method: int
    resistance: float
    reactance: float
    magnetizing_conductance: float
    magnetizing_susceptance: float
    nominal_mva: float
    from_bus_voltage: float
    to_bus_voltage: float
    min_tap: float
    max_tap: float
    step_size: float
    min_angle: float
    max_angle: float
    angle_step: float
    tap_position: float
    phase_angle: float
    name: str = ""
    brand: str = ""
    model: str = ""
    year_manufactured: int = 0
    cooling_type: str = ""
    vector_group: str = ""


@dataclass
class GeneratorData:
    """Generator data structure"""
    bus_number: int
    id: str
    active_power: float
    reactive_power: float
    max_reactive_power: float
    min_reactive_power: float
    voltage_setpoint: float
    mva_base: float
    inertia: float
    damping: float
    brand: str = ""
    model: str = ""
    fuel_type: str = ""
    efficiency: float = 0.0
    year_commissioned: int = 0


@dataclass
class LoadData:
    """Load data structure"""
    bus_number: int
    id: str
    active_power: float
    reactive_power: float
    load_type: str
    voltage_dependence: int
    area: int
    zone: int
    description: str = ""


@dataclass
class BranchData:
    """Branch data structure"""
    from_bus: int
    to_bus: int
    circuit_id: str
    resistance: float
    reactance: float
    charging_susceptance: float
    mva_rating: float
    length_km: float
    conductor_type: str = ""
    tower_type: str = ""
    brand: str = ""
    year_installed: int = 0


class EMSToPowerFactoryConverter:
    """
    Advanced converter for EMS system files to PowerFactory format
    """
    
    def __init__(self, input_file: str, output_dir: str = "output"):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize data structures
        self.buses: Dict[int, BusData] = {}
        self.transformers: List[TransformerData] = []
        self.generators: List[GeneratorData] = []
        self.loads: List[LoadData] = []
        self.branches: List[BranchData] = []
        
        # Metadata
        self.metadata = {
            "conversion_info": {
                "source_file": str(self.input_file),
                "conversion_date": datetime.now().isoformat(),
                "converter_version": "2.0.0",
                "base_frequency": 50.0,
                "system_name": "EMS Power System",
                "description": "Converted from EMS system format"
            },
            "statistics": {
                "total_buses": 0,
                "total_transformers": 0,
                "total_generators": 0,
                "total_loads": 0,
                "total_branches": 0,
                "voltage_levels": [],
                "areas": [],
                "zones": []
            },
            "brand_data": {
                "transformers": {},
                "generators": {},
                "switchgear": {},
                "protection_devices": {}
            },
            "equipment_data": {
                "transformer_models": [],
                "generator_models": [],
                "conductor_types": [],
                "tower_types": []
            }
        }
        
        # Set up logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        log_file = self.output_dir / "conversion.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def parse_ems_file(self):
        """Parse the EMS system file and extract all data sections"""
        self.logger.info(f"Parsing EMS file: {self.input_file}")
        
        print(f"Opening file: {self.input_file}")  # Debug print
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"Read {len(lines)} lines from file")  # Debug print
        except Exception as e:
            print(f"Error reading file: {e}")
            raise
            
        # Parse header information
        self._parse_header(lines)
        
        # Parse different data sections
        self._parse_bus_data(lines)
        self._parse_load_data(lines)
        self._parse_generator_data(lines)
        self._parse_branch_data(lines)
        self._parse_transformer_data(lines)
        
        # Update statistics
        self._update_statistics()
        
        self.logger.info("EMS file parsing completed successfully")
        
    def _parse_header(self, lines: List[str]):
        """Parse header information from the EMS file"""
        if len(lines) > 0:
            header_line = lines[0].strip()
            if '/' in header_line:
                parts = header_line.split('/')
                if len(parts) > 1:
                    self.metadata["conversion_info"]["description"] = parts[1].strip()
                    
        # Look for base frequency information
        for line in lines[:10]:
            if 'BASEFREQ' in line.upper():
                freq_match = re.search(r'(\d+\.?\d*)', line)
                if freq_match:
                    self.metadata["conversion_info"]["base_frequency"] = float(freq_match.group(1))
                    
    def _parse_bus_data(self, lines: List[str]):
        """Parse bus data section"""
        self.logger.info("Parsing bus data...")
        
        bus_start = 3  # Skip header lines
        bus_end = self._find_section_end(lines, bus_start, "End of Bus Data")
        
        voltage_levels = set()
        areas = set()
        zones = set()
        
        for i in range(bus_start, bus_end):
            line = lines[i].strip()
            if line and not line.startswith('0'):
                try:
                    # Parse bus data format using more robust parsing
                    # Format: bus_number 'name' base_kv type ...
                    
                    # Split by spaces but handle quoted names properly
                    parts = []
                    current_part = ""
                    in_quotes = False
                    
                    for char in line:
                        if char == "'":
                            in_quotes = not in_quotes
                            current_part += char
                        elif char == ' ' and not in_quotes:
                            if current_part:
                                parts.append(current_part)
                                current_part = ""
                        else:
                            current_part += char
                    
                    if current_part:
                        parts.append(current_part)
                    
                    if len(parts) >= 10:
                        bus_number = int(parts[0])
                        
                        # Extract name (remove quotes)
                        name = parts[1].strip("'") if len(parts) > 1 else f"BUS_{bus_number}"
                        
                        # Find base_kv, bus_type, and other parameters
                        # Look for the first numeric value after the name
                        base_kv = 0.0
                        bus_type = 1
                        
                        for j in range(2, min(len(parts), 8)):
                            if self._is_float(parts[j]):
                                base_kv = float(parts[j])
                                if j + 1 < len(parts):
                                    try:
                                        bus_type = int(float(parts[j+1]))  # Handle cases like "1.0"
                                    except:
                                        bus_type = 1
                                break
                        
                        # Extract voltage magnitude and angle
                        voltage_magnitude = 1.0
                        voltage_angle = 0.0
                        
                        # Look for voltage magnitude and angle in the line
                        for j in range(8, min(len(parts), 12)):
                            if self._is_float(parts[j]):
                                val = float(parts[j])
                                if 0.8 <= val <= 1.5:  # Likely voltage magnitude
                                    voltage_magnitude = val
                                    if j + 1 < len(parts) and self._is_float(parts[j+1]):
                                        voltage_angle = float(parts[j+1])
                                    break
                        
                        # Extract area and zone
                        area = 1
                        zone = 1
                        
                        # Look for area and zone after voltage values
                        for j in range(6, min(len(parts), 10)):
                            if self._is_float(parts[j]):
                                try:
                                    area = int(float(parts[j]))
                                except:
                                    pass
                                if j + 1 < len(parts) and self._is_float(parts[j+1]):
                                    try:
                                        zone = int(float(parts[j+1]))
                                    except:
                                        pass
                                break
                        
                        # Create bus object
                        bus = BusData(
                            bus_number=bus_number,
                            name=name,
                            base_kv=base_kv,
                            bus_type=bus_type,
                            voltage_magnitude=voltage_magnitude,
                            voltage_angle=voltage_angle,
                            area=area,
                            zone=zone,
                            max_voltage=1.1,
                            min_voltage=0.9,
                            description=f"Bus {name} {bus_number} {base_kv}kV"
                        )
                        
                        self.buses[bus_number] = bus
                        voltage_levels.add(base_kv)
                        areas.add(area)
                        zones.add(zone)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing bus line {i+1}: {line[:50]}... - {e}")
                    
        self.metadata["statistics"]["voltage_levels"] = sorted(list(voltage_levels))
        self.metadata["statistics"]["areas"] = sorted(list(areas))
        self.metadata["statistics"]["zones"] = sorted(list(zones))
        
    def _parse_load_data(self, lines: List[str]):
        """Parse load data section"""
        self.logger.info("Parsing load data...")
        
        bus_end = self._find_section_end(lines, 0, "End of Bus Data")
        load_start = bus_end + 1
        load_end = self._find_section_end(lines, load_start, "End of Load Data")
        
        for i in range(load_start, load_end):
            line = lines[i].strip()
            if line and not line.startswith('0'):
                try:
                    parts = line.split()
                    if len(parts) >= 5:
                        bus_number = int(parts[0])
                        load_id = parts[1].strip("'") if len(parts) > 1 else "1"
                        active_power = float(parts[2]) if len(parts) > 2 else 0.0
                        reactive_power = float(parts[3]) if len(parts) > 3 else 0.0
                        load_type = parts[4] if len(parts) > 4 else "1"
                        
                        load = LoadData(
                            bus_number=bus_number,
                            id=load_id,
                            active_power=active_power,
                            reactive_power=reactive_power,
                            load_type=load_type,
                            voltage_dependence=1,
                            area=1,
                            zone=1,
                            description=f"Load at bus {bus_number}"
                        )
                        
                        self.loads.append(load)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing load line {i+1}: {line[:50]}... - {e}")
                    
    def _parse_generator_data(self, lines: List[str]):
        """Parse generator data section"""
        self.logger.info("Parsing generator data...")
        
        load_end = self._find_section_end(lines, 0, "End of Load Data")
        gen_start = load_end + 1
        gen_end = self._find_section_end(lines, gen_start, "End of Generator Data")
        
        for i in range(gen_start, gen_end):
            line = lines[i].strip()
            if line and not line.startswith('0'):
                try:
                    # Parse generator data with more flexible format handling
                    parts = line.split()
                    if len(parts) >= 8:
                        bus_number = int(parts[0])
                        gen_id = parts[1].strip("'") if len(parts) > 1 else "1"
                        
                        # Find active and reactive power (look for first few numeric values)
                        active_power = 0.0
                        reactive_power = 0.0
                        max_reactive = 999.0
                        min_reactive = -999.0
                        voltage_setpoint = 1.0
                        mva_base = 100.0
                        
                        # Look for power values in the line
                        numeric_values = []
                        for j in range(2, min(len(parts), 15)):  # Check first 15 parts
                            if self._is_float(parts[j]):
                                numeric_values.append(float(parts[j]))
                        
                        if len(numeric_values) >= 2:
                            active_power = numeric_values[0]
                            reactive_power = numeric_values[1]
                            if len(numeric_values) > 2:
                                max_reactive = abs(numeric_values[2])
                                min_reactive = -abs(numeric_values[3]) if len(numeric_values) > 3 else -max_reactive
                            if len(numeric_values) > 4:
                                voltage_setpoint = numeric_values[4]
                            if len(numeric_values) > 5:
                                mva_base = numeric_values[5]
                        
                        # Extract brand information from description part
                        brand = ""
                        model = ""
                        
                        # Find description part (usually after comma-separated values)
                        desc_start = -1
                        for j, part in enumerate(parts):
                            if part.startswith("'") or part.startswith('"'):
                                desc_start = j
                                break
                        
                        if desc_start > 0:
                            desc_parts = " ".join(parts[desc_start:]).strip("'\"").split()
                            if desc_parts:
                                brand = desc_parts[0]
                                if len(desc_parts) > 1:
                                    model = " ".join(desc_parts[1:3])  # Take first few words
                        
                        generator = GeneratorData(
                            bus_number=bus_number,
                            id=gen_id,
                            active_power=active_power,
                            reactive_power=reactive_power,
                            max_reactive_power=max_reactive,
                            min_reactive_power=min_reactive,
                            voltage_setpoint=voltage_setpoint,
                            mva_base=mva_base,
                            inertia=3.0,
                            damping=0.0,
                            brand=brand,
                            model=model,
                            fuel_type="Unknown",
                            efficiency=0.95,
                            year_commissioned=2000
                        )
                        
                        self.generators.append(generator)
                        
                        # Update brand data
                        if brand:
                            self.metadata["brand_data"]["generators"][brand] = {
                                "model": model,
                                "type": "Synchronous Generator",
                                "fuel_type": "Unknown"
                            }
                            
                except Exception as e:
                    self.logger.warning(f"Error parsing generator line {i+1}: {line[:50]}... - {e}")
                    
    def _parse_branch_data(self, lines: List[str]):
        """Parse branch data section"""
        self.logger.info("Parsing branch data...")
        
        gen_end = self._find_section_end(lines, 0, "End of Generator Data")
        branch_start = gen_end + 1
        branch_end = self._find_section_end(lines, branch_start, "End of Branch Data")
        
        for i in range(branch_start, branch_end):
            line = lines[i].strip()
            if line and not line.startswith('0'):
                try:
                    parts = line.split()
                    if len(parts) >= 8:
                        from_bus = int(parts[0])
                        to_bus = int(parts[1])
                        circuit_id = parts[2].strip("'") if len(parts) > 2 else "1"
                        resistance = float(parts[3]) if len(parts) > 3 else 0.0
                        reactance = float(parts[4]) if len(parts) > 4 else 0.0
                        charging_susceptance = float(parts[5]) if len(parts) > 5 else 0.0
                        mva_rating = float(parts[6]) if len(parts) > 6 else 100.0
                        
                        branch = BranchData(
                            from_bus=from_bus,
                            to_bus=to_bus,
                            circuit_id=circuit_id,
                            resistance=resistance,
                            reactance=reactance,
                            charging_susceptance=charging_susceptance,
                            mva_rating=mva_rating,
                            length_km=1.0,
                            conductor_type="Unknown",
                            tower_type="Unknown",
                            brand="Unknown",
                            year_installed=2000
                        )
                        
                        self.branches.append(branch)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing branch line {i+1}: {line[:50]}... - {e}")
                    
    def _parse_transformer_data(self, lines: List[str]):
        """Parse transformer data section"""
        self.logger.info("Parsing transformer data...")
        
        branch_end = self._find_section_end(lines, 0, "End of Branch Data")
        transformer_start = branch_end + 1
        transformer_end = self._find_section_end(lines, transformer_start, "End of Transformer Data")
        
        i = transformer_start
        while i < transformer_end - 3:  # Need at least 4 lines for a complete transformer
            line = lines[i].strip()
            if line and not line.startswith('0'):
                try:
                    # Parse transformer header line
                    parts = line.split()
                    if len(parts) >= 8:
                        from_bus = int(parts[0])
                        to_bus = int(parts[1])
                        
                        # Read next 3 lines for complete transformer data
                        if i + 3 < transformer_end:
                            # Line 2: Impedance data
                            impedance_line = lines[i+1].strip()
                            imp_parts = impedance_line.split()
                            resistance = 0.0
                            reactance = 0.0
                            nominal_mva = 100.0
                            
                            if len(imp_parts) >= 3:
                                resistance = float(imp_parts[0])
                                reactance = float(imp_parts[1])
                                nominal_mva = float(imp_parts[2])
                            
                            # Line 3: Detailed parameters
                            param_line = lines[i+2].strip()
                            param_parts = param_line.split()
                            
                            # Extract tap position and from voltage
                            tap_position = 1.0
                            from_voltage = 110.0
                            
                            if len(param_parts) >= 2:
                                tap_position = float(param_parts[0])
                                from_voltage = float(param_parts[1])
                            
                            # Line 4: Secondary voltage and name
                            volt_line = lines[i+3].strip()
                            volt_parts = volt_line.split()
                            
                            to_voltage = 33.0
                            transformer_name = f"TX_{from_bus}_{to_bus}"
                            
                            if len(volt_parts) >= 2:
                                to_voltage = float(volt_parts[1])
                                # Extract name from the description part
                                if len(volt_parts) > 2:
                                    name_parts = " ".join(volt_parts[2:]).strip('"')
                                    if name_parts:
                                        transformer_name = name_parts.split()[0] if name_parts.split() else transformer_name
                            
                            # Create transformer object
                            transformer = TransformerData(
                                from_bus=from_bus,
                                to_bus=to_bus,
                                circuit_id="1",
                                winding_type=2,
                                control_method=1,
                                resistance=resistance,
                                reactance=reactance,
                                magnetizing_conductance=0.0,
                                magnetizing_susceptance=0.0,
                                nominal_mva=nominal_mva,
                                from_bus_voltage=from_voltage,
                                to_bus_voltage=to_voltage,
                                min_tap=0.9,
                                max_tap=1.1,
                                step_size=0.01,
                                min_angle=-30.0,
                                max_angle=30.0,
                                angle_step=1.0,
                                tap_position=tap_position,
                                phase_angle=0.0,
                                name=transformer_name,
                                brand="Unknown",
                                model="Standard",
                                year_manufactured=2000,
                                cooling_type="ONAN",
                                vector_group="YNd11"
                            )
                            
                            self.transformers.append(transformer)
                            
                            # Update brand data
                            brand_key = f"TX_{from_bus}_{to_bus}"
                            self.metadata["brand_data"]["transformers"][brand_key] = {
                                "type": "Power Transformer",
                                "voltage_ratio": f"{from_voltage}/{to_voltage}kV",
                                "mva_rating": nominal_mva,
                                "vector_group": "YNd11",
                                "cooling_type": "ONAN"
                            }
                            
                            # Skip the next 3 lines as we've processed them
                            i += 3
                            
                except Exception as e:
                    self.logger.warning(f"Error parsing transformer line {i+1}: {line[:50]}... - {e}")
            i += 1
            
    def _find_section_end(self, lines: List[str], start_line: int, marker: str) -> int:
        """Find the end of a section"""
        for i in range(start_line, len(lines)):
            if marker in lines[i]:
                return i
        return len(lines)
        
    def _is_float(self, value: str) -> bool:
        """Check if a string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    def _update_statistics(self):
        """Update system statistics"""
        self.metadata["statistics"]["total_buses"] = len(self.buses)
        self.metadata["statistics"]["total_transformers"] = len(self.transformers)
        self.metadata["statistics"]["total_generators"] = len(self.generators)
        self.metadata["statistics"]["total_loads"] = len(self.loads)
        self.metadata["statistics"]["total_branches"] = len(self.branches)
        
        # Calculate total capacity
        total_gen_capacity = sum(gen.mva_base for gen in self.generators)
        total_load_demand = sum(load.active_power for load in self.loads)
        
        self.metadata["statistics"]["total_generation_capacity_mva"] = total_gen_capacity
        self.metadata["statistics"]["total_load_demand_mw"] = total_load_demand
        
    def generate_powerfactory_raw(self, output_file: str = None) -> str:
        """Generate PowerFactory .raw file"""
        if output_file is None:
            output_file = self.output_dir / f"{self.input_file.stem}_powerfactory.raw"
        else:
            output_file = Path(output_file)
            
        self.logger.info(f"Generating PowerFactory .raw file: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"0, {self.metadata['conversion_info']['base_frequency']:.1f}, 30 / PowerFactory RAW File\n")
            f.write(f"Converted from {self.input_file.name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Base frequency: {self.metadata['conversion_info']['base_frequency']:.3f} Hz\n")
            f.write("\n")
            
            # Write bus data
            f.write("/BUS DATA\n")
            for bus in self.buses.values():
                f.write(f"{bus.bus_number}, '{bus.name}', {bus.base_kv:.2f}, {bus.bus_type}, "
                       f"{bus.voltage_magnitude:.4f}, {bus.voltage_angle:.3f}, "
                       f"{bus.area}, {bus.zone}, {bus.max_voltage:.3f}, {bus.min_voltage:.3f}\n")
            f.write("0 / End of Bus Data\n\n")
            
            # Write load data
            f.write("/LOAD DATA\n")
            for load in self.loads:
                f.write(f"{load.bus_number}, '{load.id}', {load.active_power:.2f}, {load.reactive_power:.2f}, "
                       f"{load.load_type}, {load.voltage_dependence}, {load.area}, {load.zone}\n")
            f.write("0 / End of Load Data\n\n")
            
            # Write generator data
            f.write("/GENERATOR DATA\n")
            for gen in self.generators:
                f.write(f"{gen.bus_number}, '{gen.id}', {gen.active_power:.2f}, {gen.reactive_power:.2f}, "
                       f"{gen.max_reactive_power:.2f}, {gen.min_reactive_power:.2f}, "
                       f"{gen.voltage_setpoint:.4f}, {gen.mva_base:.2f}\n")
            f.write("0 / End of Generator Data\n\n")
            
            # Write branch data
            f.write("/BRANCH DATA\n")
            for branch in self.branches:
                f.write(f"{branch.from_bus}, {branch.to_bus}, '{branch.circuit_id}', "
                       f"{branch.resistance:.6f}, {branch.reactance:.6f}, "
                       f"{branch.charging_susceptance:.6f}, {branch.mva_rating:.2f}\n")
            f.write("0 / End of Branch Data\n\n")
            
            # Write transformer data
            f.write("/TRANSFORMER DATA\n")
            for transformer in self.transformers:
                f.write(f"{transformer.from_bus}, {transformer.to_bus}, '{transformer.circuit_id}', "
                       f"{transformer.winding_type}, {transformer.control_method}, "
                       f"{transformer.resistance:.6f}, {transformer.reactance:.6f}, "
                       f"{transformer.nominal_mva:.2f}\n")
            f.write("0 / End of Transformer Data\n")
            
        self.logger.info(f"PowerFactory .raw file generated: {output_file}")
        return str(output_file)
        
    def generate_metadata_json(self, output_file: str = None) -> str:
        """Generate comprehensive metadata JSON file"""
        if output_file is None:
            output_file = self.output_dir / f"{self.input_file.stem}_metadata.json"
        else:
            output_file = Path(output_file)
            
        self.logger.info(f"Generating metadata JSON file: {output_file}")
        
        # Prepare data for JSON serialization
        metadata_copy = self.metadata.copy()
        
        # Add detailed equipment information
        equipment_data = {
            "transformers": [
                {
                    "id": f"TX_{tx.from_bus}_{tx.to_bus}",
                    "from_bus": tx.from_bus,
                    "to_bus": tx.to_bus,
                    "voltage_ratio": f"{tx.from_bus_voltage}/{tx.to_bus_voltage}kV",
                    "mva_rating": tx.nominal_mva,
                    "impedance": f"{tx.resistance}+j{tx.reactance} pu",
                    "brand": tx.brand,
                    "model": tx.model,
                    "cooling_type": tx.cooling_type,
                    "vector_group": tx.vector_group,
                    "year_manufactured": tx.year_manufactured
                }
                for tx in self.transformers
            ],
            "generators": [
                {
                    "id": f"GEN_{gen.bus_number}_{gen.id}",
                    "bus_number": gen.bus_number,
                    "mva_base": gen.mva_base,
                    "active_power": gen.active_power,
                    "reactive_power": gen.reactive_power,
                    "voltage_setpoint": gen.voltage_setpoint,
                    "brand": gen.brand,
                    "model": gen.model,
                    "fuel_type": gen.fuel_type,
                    "efficiency": gen.efficiency,
                    "year_commissioned": gen.year_commissioned
                }
                for gen in self.generators
            ],
            "buses": [
                {
                    "number": bus.bus_number,
                    "name": bus.name,
                    "base_kv": bus.base_kv,
                    "type": bus.bus_type,
                    "area": bus.area,
                    "zone": bus.zone,
                    "voltage_magnitude": bus.voltage_magnitude,
                    "voltage_angle": bus.voltage_angle
                }
                for bus in self.buses.values()
            ]
        }
        
        metadata_copy["detailed_equipment"] = equipment_data
        
        # Write JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_copy, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Metadata JSON file generated: {output_file}")
        return str(output_file)
        
    def generate_excel_report(self, output_file: str = None) -> str:
        """Generate comprehensive Excel report"""
        if output_file is None:
            output_file = self.output_dir / f"{self.input_file.stem}_report.xlsx"
        else:
            output_file = Path(output_file)
            
        self.logger.info(f"Generating Excel report: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Bus data sheet
            if self.buses:
                bus_df = pd.DataFrame([
                    {
                        "Bus Number": bus.bus_number,
                        "Name": bus.name,
                        "Base kV": bus.base_kv,
                        "Type": bus.bus_type,
                        "Voltage Mag": bus.voltage_magnitude,
                        "Voltage Angle": bus.voltage_angle,
                        "Area": bus.area,
                        "Zone": bus.zone
                    }
                    for bus in self.buses.values()
                ])
                bus_df.to_excel(writer, sheet_name='Buses', index=False)
                
            # Transformer data sheet
            if self.transformers:
                tx_df = pd.DataFrame([
                    {
                        "From Bus": tx.from_bus,
                        "To Bus": tx.to_bus,
                        "Circuit ID": tx.circuit_id,
                        "Resistance (pu)": tx.resistance,
                        "Reactance (pu)": tx.reactance,
                        "MVA Rating": tx.nominal_mva,
                        "From Voltage (kV)": tx.from_bus_voltage,
                        "To Voltage (kV)": tx.to_bus_voltage,
                        "Brand": tx.brand,
                        "Model": tx.model,
                        "Cooling Type": tx.cooling_type,
                        "Vector Group": tx.vector_group
                    }
                    for tx in self.transformers
                ])
                tx_df.to_excel(writer, sheet_name='Transformers', index=False)
                
            # Generator data sheet
            if self.generators:
                gen_df = pd.DataFrame([
                    {
                        "Bus Number": gen.bus_number,
                        "ID": gen.id,
                        "Active Power (MW)": gen.active_power,
                        "Reactive Power (MVAr)": gen.reactive_power,
                        "MVA Base": gen.mva_base,
                        "Voltage Setpoint": gen.voltage_setpoint,
                        "Brand": gen.brand,
                        "Model": gen.model,
                        "Fuel Type": gen.fuel_type,
                        "Efficiency": gen.efficiency
                    }
                    for gen in self.generators
                ])
                gen_df.to_excel(writer, sheet_name='Generators', index=False)
                
            # System summary sheet
            summary_data = {
                'Metric': [
                    'Total Buses',
                    'Total Transformers',
                    'Total Generators',
                    'Total Loads',
                    'Total Branches',
                    'Total Generation Capacity (MVA)',
                    'Total Load Demand (MW)',
                    'Base Frequency (Hz)',
                    'Voltage Levels (kV)',
                    'Number of Areas',
                    'Number of Zones'
                ],
                'Value': [
                    self.metadata['statistics']['total_buses'],
                    self.metadata['statistics']['total_transformers'],
                    self.metadata['statistics']['total_generators'],
                    self.metadata['statistics']['total_loads'],
                    self.metadata['statistics']['total_branches'],
                    self.metadata['statistics']['total_generation_capacity_mva'],
                    self.metadata['statistics']['total_load_demand_mw'],
                    self.metadata['conversion_info']['base_frequency'],
                    ', '.join(map(str, self.metadata['statistics']['voltage_levels'])),
                    len(self.metadata['statistics']['areas']),
                    len(self.metadata['statistics']['zones'])
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='System Summary', index=False)
            
        self.logger.info(f"Excel report generated: {output_file}")
        return str(output_file)
        
    def convert(self) -> Dict[str, str]:
        """Execute the complete conversion process"""
        self.logger.info("Starting EMS to PowerFactory conversion process...")
        
        try:
            # Parse input file
            self.parse_ems_file()
            
            # Generate output files
            raw_file = self.generate_powerfactory_raw()
            json_file = self.generate_metadata_json()
            excel_file = self.generate_excel_report()
            
            self.logger.info("Conversion process completed successfully!")
            
            return {
                "powerfactory_raw": raw_file,
                "metadata_json": json_file,
                "excel_report": excel_file,
                "log_file": str(self.output_dir / "conversion.log")
            }
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise


def main():
    """Main function for command-line usage"""
    print("Starting main function...")  # Debug print
    parser = argparse.ArgumentParser(
        description="Convert EMS system files to PowerFactory format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python ems_to_powerfactory_converter.py input.txt
    python ems_to_powerfactory_converter.py input.txt -o output_dir
    python ems_to_powerfactory_converter.py input.txt --raw-file custom.raw --json-file metadata.json
        """
    )
    
    parser.add_argument('input_file', help='Input EMS system .txt file')
    parser.add_argument('-o', '--output-dir', default='output', 
                       help='Output directory (default: output)')
    parser.add_argument('--raw-file', help='Custom name for PowerFactory .raw file')
    parser.add_argument('--json-file', help='Custom name for metadata JSON file')
    parser.add_argument('--excel-file', help='Custom name for Excel report file')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    print(f"Input file: {args.input_file}")  # Debug print
    print(f"Output directory: {args.output_dir}")  # Debug print
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Debug logging enabled")
    
    # Convert relative paths to absolute paths
    input_path = Path(args.input_file)
    if not input_path.is_absolute():
        input_path = Path.cwd() / input_path
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
        
    # Create converter instance
    converter = EMSToPowerFactoryConverter(str(input_path), str(output_dir))
    
    try:
        # Execute conversion
        results = converter.convert()
        
        print("\n" + "="*60)
        print("CONVERSION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"PowerFactory .raw file: {results['powerfactory_raw']}")
        print(f"Metadata JSON file: {results['metadata_json']}")
        print(f"Excel report: {results['excel_report']}")
        print(f"Log file: {results['log_file']}")
        print("="*60)
        
        # Display summary statistics
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
        
    except Exception as e:
        print(f"\nERROR: Conversion failed - {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())