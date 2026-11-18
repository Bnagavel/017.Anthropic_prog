# Beam Analysis Model Validation Framework
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from scipy import integrate
import warnings

@dataclass
class ValidationResult:
    problem_id: str
    analytical_solution: Dict
    model_solution: Dict  
    accuracy_metrics: Dict
    passed: bool
    error_analysis: Dict

class BeamAnalyticalSolver:
    """Reference analytical solver for beam problems"""
    
    @staticmethod
    def solve_simply_supported_beam(length: float, loads: List[Dict], 
                                   beam_properties: Dict) -> Dict:
        """
        Analytical solution for simply supported beam
        Returns exact solutions for validation
        """
        
        E = beam_properties['material_E']
        I = beam_properties['width'] * beam_properties['height']**3 / 12
        
        # Calculate reactions
        reactions = BeamAnalyticalSolver._calculate_reactions(length, loads)
        
        # Calculate maximum moment and its location
        max_moment, moment_location = BeamAnalyticalSolver._calculate_max_moment(
            length, loads, reactions
        )
        
        # Calculate maximum stress
        c = beam_properties['height'] / 2  # distance to extreme fiber
        max_stress = abs(max_moment) * c / I
        
        # Calculate maximum deflection
        max_deflection = BeamAnalyticalSolver._calculate_max_deflection(
            length, loads, E, I
        )
        
        # Calculate safety factor
        yield_strength = beam_properties['material_yield']
        safety_factor = yield_strength / max_stress if max_stress > 0 else float('inf')
        
        return {
            'reactions': reactions,
            'max_moment': max_moment,
            'moment_location': moment_location,
            'max_stress': max_stress,
            'max_deflection': max_deflection,
            'safety_factor': safety_factor,
            'moment_of_inertia': I
        }
    
    @staticmethod
    def _calculate_reactions(length: float, loads: List[Dict]) -> Dict:
        """Calculate support reactions using equilibrium equations"""
        
        sum_forces = 0
        sum_moments_about_left = 0
        
        for load in loads:
            if load['type'] == 'point':
                F = load['magnitude']
                a = load['position']
                sum_forces += F
                sum_moments_about_left += F * a
                
            elif load['type'] == 'distributed':
                w = load['magnitude']  # load per unit length
                a = load['position']   # start position
                b = load.get('end_position', length)  # end position
                load_length = b - a
                total_load = w * load_length
                centroid = a + load_length / 2
                
                sum_forces += total_load
                sum_moments_about_left += total_load * centroid
        
        # Right reaction from moment equilibrium
        R_right = sum_moments_about_left / length
        
        # Left reaction from force equilibrium
        R_left = sum_forces - R_right
        
        return {'left': R_left, 'right': R_right}
    
    @staticmethod
    def _calculate_max_moment(length: float, loads: List[Dict], reactions: Dict) -> Tuple[float, float]:
        """Calculate maximum bending moment and its location"""
        
        x_points = np.linspace(0, length, 1000)
        moments = []
        
        for x in x_points:
            M = BeamAnalyticalSolver._moment_at_x(x, length, loads, reactions)
            moments.append(M)
        
        moments = np.array(moments)
        max_moment_idx = np.argmax(np.abs(moments))
        max_moment = moments[max_moment_idx]
        moment_location = x_points[max_moment_idx]
        
        return max_moment, moment_location
    
    @staticmethod
    def _moment_at_x(x: float, length: float, loads: List[Dict], reactions: Dict) -> float:
        """Calculate bending moment at position x"""
        
        # Start with moment from left reaction
        M = reactions['left'] * x
        
        # Subtract moments from loads to the left of x
        for load in loads:
            if load['type'] == 'point':
                if load['position'] <= x:
                    M -= load['magnitude'] * (x - load['position'])
                    
            elif load['type'] == 'distributed':
                a = load['position']
                b = load.get('end_position', length)
                w = load['magnitude']
                
                if b <= x:
                    # Entire distributed load to the left
                    load_length = b - a
                    total_load = w * load_length
                    centroid = a + load_length / 2
                    M -= total_load * (x - centroid)
                    
                elif a <= x < b:
                    # Partial distributed load to the left
                    partial_length = x - a
                    partial_load = w * partial_length
                    partial_centroid = a + partial_length / 2
                    M -= partial_load * (x - partial_centroid)
        
        return M
    
    @staticmethod
    def _calculate_max_deflection(length: float, loads: List[Dict], E: float, I: float) -> float:
        """Calculate maximum deflection using analytical formulas"""
        
        # For complex loading, use superposition principle
        total_deflection = 0
        
        for load in loads:
            if load['type'] == 'point':
                deflection = BeamAnalyticalSolver._point_load_deflection(
                    load['magnitude'], load['position'], length, E, I
                )
                total_deflection += deflection
                
            elif load['type'] == 'distributed':
                deflection = BeamAnalyticalSolver._distributed_load_deflection(
                    load['magnitude'], load['position'], 
                    load.get('end_position', length), length, E, I
                )
                total_deflection += deflection
        
        return abs(total_deflection)
    
    @staticmethod
    def _point_load_deflection(P: float, a: float, L: float, E: float, I: float) -> float:
        """Maximum deflection for point load on simply supported beam"""
        
        b = L - a
        
        # Maximum deflection occurs at different locations based on load position
        if a <= L/2:
            # Load in left half - max deflection under load
            delta = (P * b * (L**2 - b**2)**1.5) / (9 * np.sqrt(3) * E * I * L)
        else:
            # Load in right half - max deflection under load  
            delta = (P * a * (L**2 - a**2)**1.5) / (9 * np.sqrt(3) * E * I * L)
            
        return delta
    
    @staticmethod 
    def _distributed_load_deflection(w: float, a: float, b: float, L: float, E: float, I: float) -> float:
        """Maximum deflection for distributed load on simply supported beam"""
        
        # Simplified approach - treat as point load at centroid
        load_length = b - a
        total_load = w * load_length
        centroid = a + load_length / 2
        
        return BeamAnalyticalSolver._point_load_deflection(total_load, centroid, L, E, I)

class ModelOutputParser:
    """Parse model-generated solutions and extract numerical values"""
    
    @staticmethod
    def parse_solution(solution_text: str) -> Dict:
        """Extract numerical values from model solution"""
        
        parsed = {}
        
        # Patterns for different quantities
        patterns = {
            'left_reaction': [
                r'left reaction[:\s]*([0-9.,]+)\s*(kn|n)',
                r'r_left[:\s=]*([0-9.,]+)\s*(kn|n)',
                r'reaction.*left[:\s]*([0-9.,]+)\s*(kn|n)'
            ],
            'right_reaction': [
                r'right reaction[:\s]*([0-9.,]+)\s*(kn|n)',
                r'r_right[:\s=]*([0-9.,]+)\s*(kn|n)',
                r'reaction.*right[:\s]*([0-9.,]+)\s*(kn|n)'
            ],
            'max_stress': [
                r'maximum stress[:\s]*([0-9.,]+)\s*(mpa|pa)',
                r'max.*stress[:\s]*([0-9.,]+)\s*(mpa|pa)',
                r'σ_max[:\s=]*([0-9.,]+)\s*(mpa|pa)'
            ],
            'max_deflection': [
                r'maximum deflection[:\s]*([0-9.,]+)\s*(mm|m)',
                r'max.*deflection[:\s]*([0-9.,]+)\s*(mm|m)',
                r'δ_max[:\s=]*([0-9.,]+)\s*(mm|m)'
            ],
            'safety_factor': [
                r'safety factor[:\s]*([0-9.,]+)',
                r'sf[:\s=]*([0-9.,]+)',
                r'factor.*safety[:\s]*([0-9.,]+)'
            ]
        }
        
        solution_lower = solution_text.lower()
        
        for quantity, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, solution_lower)
                if match:
                    value_str = match.group(1).replace(',', '')
                    try:
                        value = float(value_str)
                        unit = match.group(2) if len(match.groups()) > 1 else None
                        
                        # Convert to standard units
                        if quantity in ['left_reaction', 'right_reaction']:
                            if unit and 'kn' in unit:
                                value *= 1000  # Convert kN to N
                        elif quantity == 'max_stress':
                            if unit and 'mpa' in unit:
                                value *= 1e6  # Convert MPa to Pa
                        elif quantity == 'max_deflection':
                            if unit and 'mm' in unit:
                                value *= 1e-3  # Convert mm to m
                                
                        parsed[quantity] = value
                        break
                    except ValueError:
                        continue
        
        return parsed

class BeamValidationFramework:
    """Comprehensive validation framework for beam analysis models"""
    
    def __init__(self, tolerance_percent: float = 5.0):
        self.tolerance_percent = tolerance_percent
        self.analytical_solver = BeamAnalyticalSolver()
        self.parser = ModelOutputParser()
        
    def validate_model_solution(self, problem: Dict, model_solution: str) -> ValidationResult:
        """Validate a single model solution against analytical solution"""
        
        # Get analytical solution
        analytical = self.analytical_solver.solve_simply_supported_beam(
            problem['beam_properties']['length'],
            problem['loads'],
            problem['beam_properties']
        )
        
        # Parse model solution
        parsed_model = self.parser.parse_solution(model_solution)
        
        # Calculate accuracy metrics
        accuracy_metrics = self._calculate_accuracy_metrics(analytical, parsed_model)
        
        # Determine if validation passed
        passed = self._check_validation_pass(accuracy_metrics)
        
        # Error analysis
        error_analysis = self._perform_error_analysis(analytical, parsed_model)
        
        return ValidationResult(
            problem_id=problem.get('id', 'unknown'),
            analytical_solution=analytical,
            model_solution=parsed_model,
            accuracy_metrics=accuracy_metrics,
            passed=passed,
            error_analysis=error_analysis
        )
    
    def _calculate_accuracy_metrics(self, analytical: Dict, model: Dict) -> Dict:
        """Calculate accuracy metrics for each quantity"""
        
        metrics = {}
        
        # Compare reactions
        if 'left_reaction' in model and 'right_reaction' in model:
            left_error = abs(analytical['reactions']['left'] - model['left_reaction'])
            right_error = abs(analytical['reactions']['right'] - model['right_reaction'])
            
            left_percent_error = (left_error / abs(analytical['reactions']['left'])) * 100 if analytical['reactions']['left'] != 0 else 0
            right_percent_error = (right_error / abs(analytical['reactions']['right'])) * 100 if analytical['reactions']['right'] != 0 else 0
            
            metrics['reactions'] = {
                'left_percent_error': left_percent_error,
                'right_percent_error': right_percent_error,
                'average_error': (left_percent_error + right_percent_error) / 2
            }
        
        # Compare stress
        if 'max_stress' in model:
            stress_error = abs(analytical['max_stress'] - model['max_stress'])
            stress_percent_error = (stress_error / analytical['max_stress']) * 100
            metrics['stress'] = {'percent_error': stress_percent_error}
        
        # Compare deflection  
        if 'max_deflection' in model:
            deflection_error = abs(analytical['max_deflection'] - model['max_deflection'])
            deflection_percent_error = (deflection_error / analytical['max_deflection']) * 100
            metrics['deflection'] = {'percent_error': deflection_percent_error}
        
        # Compare safety factor
        if 'safety_factor' in model:
            sf_error = abs(analytical['safety_factor'] - model['safety_factor'])
            sf_percent_error = (sf_error / analytical['safety_factor']) * 100
            metrics['safety_factor'] = {'percent_error': sf_percent_error}
        
        return metrics
    
    def _check_validation_pass(self, accuracy_metrics: Dict) -> bool:
        """Check if validation passes based on tolerance"""
        
        for category, metrics in accuracy_metrics.items():
            if isinstance(metrics, dict):
                if 'percent_error' in metrics:
                    if metrics['percent_error'] > self.tolerance_percent:
                        return False
                elif 'average_error' in metrics:
                    if metrics['average_error'] > self.tolerance_percent:
                        return False
        
        return True
    
    def _perform_error_analysis(self, analytical: Dict, model: Dict) -> Dict:
        """Analyze types and sources of errors"""
        
        analysis = {
            'missing_quantities': [],
            'unit_errors': [],
            'calculation_errors': [],
            'parsing_errors': []
        }
        
        # Check for missing quantities
        expected_quantities = ['left_reaction', 'right_reaction', 'max_stress', 'safety_factor']
        for qty in expected_quantities:
            if qty not in model:
                analysis['missing_quantities'].append(qty)
        
        # Check for unrealistic values (potential unit errors)
        if 'max_stress' in model:
            if model['max_stress'] > 1e9:  # > 1 GPa (likely unit error)
                analysis['unit_errors'].append('max_stress_too_high')
            elif model['max_stress'] < 1e3:  # < 1 kPa (likely unit error)
                analysis['unit_errors'].append('max_stress_too_low')
        
        if 'max_deflection' in model:
            if model['max_deflection'] > 1.0:  # > 1 m (likely unit error)
                analysis['unit_errors'].append('max_deflection_too_high')
        
        return analysis
    
    def run_validation_suite(self, test_problems: List[Dict], model_inference_func) -> Dict:
        """Run complete validation suite on multiple problems"""
        
        results = []
        
        for i, problem in enumerate(test_problems):
            print(f"Validating problem {i+1}/{len(test_problems)}...")
            
            # Get model solution
            try:
                model_solution = model_inference_func(problem['problem_text'])
                validation_result = self.validate_model_solution(problem, model_solution)
                results.append(validation_result)
                
            except Exception as e:
                print(f"Error validating problem {i+1}: {str(e)}")
                continue
        
        # Generate summary statistics
        summary = self._generate_validation_summary(results)
        
        return {
            'individual_results': results,
            'summary': summary
        }
    
    def _generate_validation_summary(self, results: List[ValidationResult]) -> Dict:
        """Generate summary statistics from validation results"""
        
        total_problems = len(results)
        passed_problems = sum(1 for r in results if r.passed)
        pass_rate = (passed_problems / total_problems) * 100 if total_problems > 0 else 0
        
        # Average errors by category
        category_errors = {}
        for result in results:
            for category, metrics in result.accuracy_metrics.items():
                if category not in category_errors:
                    category_errors[category] = []
                
                if isinstance(metrics, dict):
                    if 'percent_error' in metrics:
                        category_errors[category].append(metrics['percent_error'])
                    elif 'average_error' in metrics:
                        category_errors[category].append(metrics['average_error'])
        
        average_errors = {}
        for category, errors in category_errors.items():
            if errors:
                average_errors[category] = {
                    'mean': np.mean(errors),
                    'std': np.std(errors),
                    'max': np.max(errors),
                    'min': np.min(errors)
                }
        
        return {
            'total_problems': total_problems,
            'passed_problems': passed_problems,
            'pass_rate_percent': pass_rate,
            'average_errors_by_category': average_errors
        }

# Test data generator for validation
class ValidationTestSuite:
    """Generate test problems for model validation"""
    
    @staticmethod
    def generate_test_problems(num_problems: int = 50) -> List[Dict]:
        """Generate diverse test problems for validation"""
        
        from beam_analysis_data import BeamAnalysisGenerator
        
        generator = BeamAnalysisGenerator()
        test_problems = []
        
        for i in range(num_problems):
            problem = generator.generate_beam_problem()
            problem['id'] = f"test_{i+1}"
            test_problems.append(problem)
        
        return test_problems
    
    @staticmethod
    def create_benchmark_problems() -> List[Dict]:
        """Create specific benchmark problems with known solutions"""
        
        benchmarks = []
        
        # Simple point load at center
        benchmarks.append({
            'id': 'benchmark_point_center',
            'problem_text': """
            A simply supported beam with:
            - Length: 4.0 m  
            - Cross-section: 100 mm × 200 mm rectangular
            - Material: Steel A36 (E = 200 GPa, yield = 250 MPa)
            - Point load: 10 kN at center (2.0 m)
            
            Calculate reactions, maximum stress, and safety factor.
            """,
            'beam_properties': {
                'length': 4.0,
                'width': 0.1,
                'height': 0.2,
                'material_E': 200e9,
                'material_yield': 250e6
            },
            'loads': [{'type': 'point', 'magnitude': 10000, 'position': 2.0}]
        })
        
        # Uniform distributed load
        benchmarks.append({
            'id': 'benchmark_uniform_load',
            'problem_text': """
            A simply supported beam with:
            - Length: 6.0 m
            - Cross-section: 150 mm × 300 mm rectangular  
            - Material: Aluminum 6061 (E = 69 GPa, yield = 276 MPa)
            - Uniform distributed load: 5 kN/m over entire span
            
            Calculate reactions, maximum stress, and safety factor.
            """,
            'beam_properties': {
                'length': 6.0,
                'width': 0.15,
                'height': 0.3,
                'material_E': 69e9,
                'material_yield': 276e6
            },
            'loads': [{'type': 'distributed', 'magnitude': 5000, 'position': 0.0, 'end_position': 6.0}]
        })
        
        return benchmarks

# Example usage and testing
def run_validation_example():
    """Example of running the validation framework"""
    
    # Generate test problems
    print("Generating test problems...")
    test_problems = ValidationTestSuite.generate_test_problems(10)
    benchmark_problems = ValidationTestSuite.create_benchmark_problems()
    all_problems = test_problems + benchmark_problems
    
    # Mock model inference function for testing
    def mock_model_inference(problem_text: str) -> str:
        """Mock model that returns approximate solutions with some errors"""
        
        # This would be replaced with actual model inference
        if "10 kN" in problem_text and "center" in problem_text:
            return """
            Solution:
            Left reaction: 5.0 kN
            Right reaction: 5.0 kN
            Maximum stress: 7.5 MPa
            Safety factor: 33.3
            """
        else:
            return """
            Solution:  
            Left reaction: 15.2 kN
            Right reaction: 14.8 kN
            Maximum stress: 12.4 MPa
            Safety factor: 20.2
            """
    
    # Run validation
    print("Running validation suite...")
    validator = BeamValidationFramework(tolerance_percent=10.0)
    validation_results = validator.run_validation_suite(all_problems, mock_model_inference)
    
    # Print results
    print(f"\nValidation Results:")
    print(f"Total problems: {validation_results['summary']['total_problems']}")
    print(f"Passed problems: {validation_results['summary']['passed_problems']}")
    print(f"Pass rate: {validation_results['summary']['pass_rate_percent']:.1f}%")
    
    print(f"\nAverage errors by category:")
    for category, stats in validation_results['summary']['average_errors_by_category'].items():
        print(f"  {category}: {stats['mean']:.2f}% ± {stats['std']:.2f}%")

if __name__ == "__main__":
    run_validation_example()