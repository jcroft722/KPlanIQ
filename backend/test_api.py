import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check Response:", response.json())

def test_file_upload():
    files = {'file': ('test_data.csv', open('test_data.csv', 'rb'), 'text/csv')}
    response = requests.post(f"{BASE_URL}/api/files/upload", files=files)
    print("File Upload Response:", response.json())

def test_list_uploads():
    response = requests.get(f"{BASE_URL}/api/files/uploads")
    print("List Uploads Response:", response.json())

if __name__ == "__main__":
    print("Testing API endpoints...")
    try:
        test_health()
        test_file_upload()
        test_list_uploads()
    except Exception as e:
        print(f"Error testing API: {str(e)}") 