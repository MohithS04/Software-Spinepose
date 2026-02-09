import requests
import os
import sys

# Configuration
URL = "http://localhost:8000/analyze_file"
IMAGE_PATH = "spine_db/images/c9596f14-2bc9-4e4c-b6d6-159a38e04e94.jpg"

def test_upload():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image file not found at {IMAGE_PATH}")
        # Try to find any jpg in the current directory or subdirectories if specific file is missing
        # For now, just exit
        sys.exit(1)

    print(f"Testing upload with {IMAGE_PATH}...")
    
    try:
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": f}
            response = requests.post(URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response JSON keys:", list(data.keys()))
            
            if "metrics" in data:
                print("Metrics:", data["metrics"])
            
            if "report" in data:
                print("Report Preview:", data["report"][:100] + "...")
                
            print("\nTest PASSED")
        else:
            print(f"Response Content: {response.text}")
            print("\nTest FAILED")

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library is missing. Please run 'pip install requests'")
        sys.exit(1)
        
    test_upload()
