import requests
import json

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


def test_api():
    # Define the base URL of your API
    base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain
    
    # Define the endpoint URL
    endpoint_url = base_url + "/get_file" #?file_id=1F4D-A0OOTEP91ArgMYohEbbOpHKsgWT3"  # Update YOUR_FILE_ID with the actual file ID
    
    try:
        # Make a GET request to the API endpoint
        response = requests.get(endpoint_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the content of the file to the console
            print(response.text)
        else:
            # Print an error message if the request was not successful
            print("Error: Unable to retrieve file. Status code:", response.status_code)
    
    except requests.RequestException as e:
        # Print an error message if an exception occurs during the request
        print("Error:", e)


base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com/create_file"
def trigger_create_file_endpoint():
    try:
        # Make a POST request to the API endpoint
        response = requests.post(base_url)
            
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("File created successfully.")
            response_data = json.loads(response.text)
            file_id = response_data.get('file_id')
            if file_id:
                print("File ID:", file_id)
            else:
                print("File ID not found in response.")
        else:
            print("Failed to create file. Status code:", response.status_code)
            print("Response:", response.text)
        
    except Exception as e:
        print("Error occurred:", str(e))

if __name__ == "__main__":
    #test_list_files_endpoint()
    test_api()
    #trigger_create_file_endpoint()

