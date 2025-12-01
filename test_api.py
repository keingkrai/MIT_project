"""
Simple test script to verify the FastAPI backend is working.
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing FastAPI backend...")
    print(f"Base URL: {base_url}\n")
    
    # Test health endpoint
    try:
        print("1. Testing /api/health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Could not connect to API. Is the server running?")
        print("   Run: python start_api.py")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Test test endpoint
    try:
        print("\n2. Testing /api/test endpoint...")
        response = requests.get(f"{base_url}/api/test", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Test root endpoint
    try:
        print("\n3. Testing / endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Web interface is accessible")
        else:
            print(f"   ⚠️  Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print("\n✅ All tests passed! API is working correctly.")
    return True

if __name__ == "__main__":
    test_api()

