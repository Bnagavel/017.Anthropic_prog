# Beam Analysis Data Generation for Foundation Model Training
import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from dataclasses import dataclass
import random

@dataclass
class BeamProperties:
    length: float  # meters
    width: float   # meters  
    height: float  # meters
    material_E: float  # Young's modulus (Pa)
    material_density: float  # kg/m³
    material_yield: float  # Pa

@dataclass
class Load:
    type: str  # 'point' or 'distributed'
    magnitude: float  # N or N/m
    position: float  # m from left end
    end_position: float = None  # for distributed loads

class BeamAnalysisGenerator:
    """Generate synthetic beam analysis problems with solutions"""
    
    def __init__(self):
        # Common materials database
        self.materials = {
            'aluminum_6061': {'E': 69e9, 'density': 2700, 'yield': 276e6},
            'steel_a36': {'E': 200e9, 'density': 7850, 'yield': 250e6},
            'titanium_ti6al4v': {'E': 114e9, 'density': 4430, 'yield': 880e6},
            'carbon_fiber': {'E': 150e9, 'density': 1600, 'yield': 600e6}
        }
        
    def generate_beam_problem(self) -> Dict:
        """Generate a single beam analysis problem"""
        
        # Random beam geometry
        length = random.uniform(1.0, 10.0)  # 1-10m
        width = random.uniform(0.05, 0.3)   # 50-300mm
        height = random.uniform(0.1, 0.5)   # 100-500mm
        
        # Random material
        material_name = random.choice(list(self.materials.keys()))
        material = self.materials[material_name]
        
        beam = BeamProperties(
            length=length,
            width=width,
            height=height,
            material_E=material['E'],
            material_density=material['density'],
            material_yield=material['yield']
        )
        
        # Generate loads
        loads = self._generate_loads(length)
        
        # Calculate analytical solution
        solution = self._calculate_analytical_solution(beam, loads)
        
        # Create problem description
        problem_text = self._create_problem_description(beam, loads, material_name)
        
        return {
            'problem_text': problem_text,
            'beam_properties': beam.__dict__,
            'loads': [load.__dict__ for load in loads],
            'material_name': material_name,
            'solution': solution,
            'calculations': self._create_step_by_step_solution(beam, loads, solution)
        }
    
    def _generate_loads(self, beam_length: float) -> List[Load]:
        """Generate random loading conditions"""
        loads = []
        num_loads = random.randint(1, 3)
        
        for _ in range(num_loads):
            load_type = random.choice(['point', 'distributed'])
            
            if load_type == 'point':
                # Point load
                magnitude = random.uniform(1000, 50000)  # 1-50 kN
                position = random.uniform(0.1 * beam_length, 0.9 * beam_length)
                loads.append(Load('point', magnitude, position))
            else:
                # Distributed load
                magnitude = random.uniform(1000, 10000)  # 1-10 kN/m
                start_pos = random.uniform(0.1 * beam_length, 0.6 * beam_length)
                end_pos = random.uniform(start_pos + 0.1 * beam_length, 0.9 * beam_length)
                loads.append(Load('distributed', magnitude, start_pos, end_pos))
        
        return loads
    
    def _calculate_analytical_solution(self, beam: BeamProperties, loads: List[Load]) -> Dict:
        """Calculate analytical solution using beam theory"""
        
        # Calculate second moment of area (rectangular cross-section)
        I = (beam.width * beam.height**3) / 12
        
        # Calculate reactions (simply supported beam)
        total_moment_about_left = 0
        total_vertical_force = 0
        
        for load in loads:
            if load.type == 'point':
                total_moment_about_left += load.magnitude * load.position
                total_vertical_force += load.magnitude
            else:  # distributed load
                load_length = load.end_position - load.position
                total_load = load.magnitude * load_length
                centroid = load.position + load_length / 2
                total_moment_about_left += total_load * centroid
                total_vertical_force += total_load
        
        # Right reaction
        R_right = total_moment_about_left / beam.length
        # Left reaction
        R_left = total_vertical_force - R_right
        
        # Calculate maximum deflection (approximate for complex loading)
        max_deflection = self._calculate_max_deflection(beam, loads, I)
        
        # Calculate maximum stress
        max_moment = self._calculate_max_moment(beam, loads, R_left, R_right)
        max_stress = abs(max_moment) * (beam.height / 2) / I
        
        # Safety factor
        safety_factor = beam.material_yield / max_stress if max_stress > 0 else float('inf')
        
        return {
            'reactions': {'left': R_left, 'right': R_right},
            'max_deflection': max_deflection,
            'max_moment': max_moment,
            'max_stress': max_stress,
            'safety_factor': safety_factor,
            'moment_of_inertia': I
        }
    
    def _calculate_max_deflection(self, beam: BeamProperties, loads: List[Load], I: float) -> float:
        """Simplified deflection calculation"""
        # This is a simplified approach - in practice, you'd use more sophisticated methods
        total_deflection = 0
        
        for load in loads:
            if load.type == 'point':
                # Point load deflection at center (approximation)
                a = load.position
                b = beam.length - a
                if a <= beam.length / 2:
                    deflection = (load.magnitude * b * (beam.length**2 - b**2)**1.5) / (9 * np.sqrt(3) * beam.material_E * I * beam.length)
                else:
                    deflection = (load.magnitude * a * (beam.length**2 - a**2)**1.5) / (9 * np.sqrt(3) * beam.material_E * I * beam.length)
                total_deflection += abs(deflection)
        
        return total_deflection
    
    def _calculate_max_moment(self, beam: BeamProperties, loads: List[Load], R_left: float, R_right: float) -> float:
        """Calculate maximum bending moment"""
        # Sample points along beam and find maximum moment
        x_points = np.linspace(0, beam.length, 100)
        moments = []
        
        for x in x_points:
            moment = R_left * x
            
            # Subtract moments from loads to the left of x
            for load in loads:
                if load.type == 'point' and load.position <= x:
                    moment -= load.magnitude * (x - load.position)
                elif load.type == 'distributed':
                    if load.end_position <= x:
                        # Entire distributed load to the left
                        load_total = load.magnitude * (load.end_position - load.position)
                        centroid = (load.position + load.end_position) / 2
                        moment -= load_total * (x - centroid)
                    elif load.position <= x < load.end_position:
                        # Partial distributed load to the left
                        partial_length = x - load.position
                        partial_load = load.magnitude * partial_length
                        partial_centroid = load.position + partial_length / 2
                        moment -= partial_load * (x - partial_centroid)
            
            moments.append(abs(moment))
        
        return max(moments)
    
    def _create_problem_description(self, beam: BeamProperties, loads: List[Load], material_name: str) -> str:
        """Create natural language problem description"""
        
        description = f"""
        BEAM ANALYSIS PROBLEM:
        
        A simply supported beam with the following properties:
        - Length: {beam.length:.2f} m
        - Cross-section: {beam.width*1000:.1f} mm × {beam.height*1000:.1f} mm rectangular
        - Material: {material_name.replace('_', ' ').title()}
        - Young's Modulus: {beam.material_E/1e9:.1f} GPa
        - Yield Strength: {beam.material_yield/1e6:.1f} MPa
        
        Loading conditions:
        """
        
        for i, load in enumerate(loads, 1):
            if load.type == 'point':
                description += f"- Point load {i}: {load.magnitude/1000:.1f} kN at {load.position:.2f} m from left support\n"
            else:
                description += f"- Distributed load {i}: {load.magnitude/1000:.1f} kN/m from {load.position:.2f} m to {load.end_position:.2f} m\n"
        
        description += "\nCalculate: reactions, maximum deflection, maximum stress, and safety factor."
        
        return description.strip()
    
    def _create_step_by_step_solution(self, beam: BeamProperties, loads: List[Load], solution: Dict) -> str:
        """Create detailed solution steps"""
        
        steps = f"""
        SOLUTION STEPS:
        
        1. Calculate second moment of area:
           I = bh³/12 = ({beam.width:.3f} × {beam.height:.3f}³)/12 = {solution['moment_of_inertia']:.2e} m⁴
        
        2. Calculate support reactions:
           Left reaction: {solution['reactions']['left']/1000:.2f} kN
           Right reaction: {solution['reactions']['right']/1000:.2f} kN
        
        3. Calculate maximum bending moment:
           M_max = {solution['max_moment']/1000:.2f} kN⋅m
        
        4. Calculate maximum stress:
           σ_max = M⋅c/I = {solution['max_stress']/1e6:.2f} MPa
        
        5. Calculate safety factor:
           SF = σ_yield/σ_max = {solution['safety_factor']:.2f}
        
        6. Calculate maximum deflection:
           δ_max = {solution['max_deflection']*1000:.3f} mm
        """
        
        return steps.strip()

# Generate training dataset
def generate_training_dataset(num_samples: int = 1000) -> pd.DataFrame:
    """Generate training dataset with beam analysis problems"""
    
    generator = BeamAnalysisGenerator()
    dataset = []
    
    print(f"Generating {num_samples} beam analysis problems...")
    
    for i in range(num_samples):
        if i % 100 == 0:
            print(f"Generated {i}/{num_samples} samples...")
            
        problem = generator.generate_beam_problem()
        
        # Create training examples in different formats
        
        # Format 1: Problem -> Solution
        dataset.append({
            'input': problem['problem_text'],
            'output': problem['calculations'],
            'type': 'problem_solution'
        })
        
        # Format 2: Problem -> Specific answers
        dataset.append({
            'input': problem['problem_text'] + "\n\nWhat is the maximum stress?",
            'output': f"The maximum stress is {problem['solution']['max_stress']/1e6:.2f} MPa",
            'type': 'specific_question'
        })
        
        # Format 3: Code generation
        dataset.append({
            'input': f"Write Python code to solve this beam analysis problem: {problem['problem_text']}",
            'output': generate_solution_code(problem),
            'type': 'code_generation'
        })
    
    print(f"Generated {len(dataset)} training examples total.")
    return pd.DataFrame(dataset)

def generate_solution_code(problem: Dict) -> str:
    """Generate Python code solution"""
    
    beam = problem['beam_properties']
    loads = problem['loads']
    
    code = f"""
import numpy as np

# Beam properties
length = {beam['length']:.3f}  # m
width = {beam['width']:.3f}   # m
height = {beam['height']:.3f}  # m
E = {beam['material_E']:.0f}   # Pa
yield_strength = {beam['material_yield']:.0f}  # Pa

# Calculate second moment of area
I = (width * height**3) / 12

# Define loads
loads = {loads}

# Calculate reactions and analysis
def analyze_beam(length, loads, E, I, yield_strength):
    # Implementation would go here
    # This is a simplified version for demonstration
    
    # Calculate reactions
    total_moment = 0
    total_force = 0
    
    for load in loads:
        if load['type'] == 'point':
            total_moment += load['magnitude'] * load['position']
            total_force += load['magnitude']
        # Add distributed load calculations...
    
    R_right = total_moment / length
    R_left = total_force - R_right
    
    return {{
        'reactions': {{'left': R_left, 'right': R_right}},
        'max_stress': {problem['solution']['max_stress']:.0f},
        'safety_factor': {problem['solution']['safety_factor']:.2f}
    }}

result = analyze_beam(length, loads, E, I, yield_strength)
print(f"Maximum stress: {{result['max_stress']/1e6:.2f}} MPa")
print(f"Safety factor: {{result['safety_factor']:.2f}}")
"""
    
    return code.strip()

# Example usage
if __name__ == "__main__":
    # Generate sample dataset
    dataset = generate_training_dataset(100)  # Small sample for testing
    
    # Save dataset
    dataset.to_csv('beam_analysis_dataset.csv', index=False)
    dataset.to_json('beam_analysis_dataset.json', orient='records', indent=2)
    
    print("Dataset saved to beam_analysis_dataset.csv and .json")
    print(f"Dataset shape: {dataset.shape}")
    print("\nSample entries:")
    for i in range(3):
        print(f"\n--- Example {i+1} ---")
        print(f"Type: {dataset.iloc[i]['type']}")
        print(f"Input: {dataset.iloc[i]['input'][:200]}...")
        print(f"Output: {dataset.iloc[i]['output'][:200]}...")
