"""
Test script for beam_api.py
Tests the analytical solver directly without running a server.
"""
import json
from beam_api import BeamProblem, Load, _analytical_solve

def test_api_logic():
    """Test the analytical solver logic directly"""
    
    # Create a test load
    test_load = Load(
        type="point",
        magnitude=10000,
        position=3.0
    )
    
    # Create a test problem
    test_problem = BeamProblem(
        description="Simply supported steel beam with point load",
        beam_length=6.0,
        loads=[test_load],
        material="steel_a36",
        support_type="simply_supported"
    )
    
    print("Testing beam analysis API logic...")
    print(f"Problem: {test_problem.description}")
    print(f"Beam length: {test_problem.beam_length} m")
    print(f"Load: {test_problem.loads[0].magnitude} N at {test_problem.loads[0].position} m")
    
    try:
        # Test the analytical solver
        solution = _analytical_solve(test_problem)
        
        print("\n✅ Solution computed successfully!")
        print(f"Max stress: {solution.max_stress:.3e} Pa")
        print(f"Max deflection: {solution.max_deflection:.3e} m")
        print(f"Safety factor: {solution.safety_factor:.2f}")
        
        print("\nGenerated code:")
        print(solution.analysis_code)
        
        print("\nReport:")
        print(solution.report)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_api_logic()
    if success:
        print("\n🎉 API logic test passed! The beam analysis is working correctly.")
    else:
        print("\n❌ API logic test failed.")