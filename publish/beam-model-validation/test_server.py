"""
Simple server test that starts the API and makes a request
"""
import subprocess
import time
import requests
import json
from pathlib import Path

def test_api_server():
    """Start server and test it"""
    
    # Start the server in background
    python_exe = Path("<WORKSPACE>/006.BeamFoundationModel_Training/.venv/Scripts/python.exe")
    
    print("Starting FastAPI server...")
    server_process = subprocess.Popen([
        str(python_exe), "-m", "uvicorn", "beam_api:app", 
        "--host", "127.0.0.1", "--port", "8000"
    ], cwd=".")
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8000/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # Test beam analysis endpoint
        print("\nTesting beam analysis endpoint...")
        test_data = {
            "description": "Simply supported steel beam with point load",
            "beam_length": 6.0,
            "loads": [{"type": "point", "magnitude": 10000, "position": 3.0}],
            "material": "steel_a36",
            "support_type": "simply_supported"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/analyze_beam",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API test successful!")
            print(f"Max stress: {result['max_stress']:.3e} Pa")
            print(f"Max deflection: {result['max_deflection']:.3e} m")
            print(f"Safety factor: {result['safety_factor']:.2f}")
        else:
            print(f"❌ API test failed: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    finally:
        # Stop the server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_api_server()