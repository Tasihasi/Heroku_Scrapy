import requests

# URL of your Flask API endpoint
API_ENDPOINT = 'https://herokuscrapy-8d468df2dace.herokuapp.com/list_files'  # Update with your actual API endpoint URL

def test_list_files_endpoint():
    # Send a GET request to the API endpoint
    response = requests.get(API_ENDPOINT)

    # Print the response status code
    print(f"Response Status Code: {response.status_code}")

    # Print the response content
    print("Response Content:")
    print(response.json())

if __name__ == "__main__":
    test_list_files_endpoint()
