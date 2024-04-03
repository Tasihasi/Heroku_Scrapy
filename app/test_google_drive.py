import requests
import json

# URL of your Flask API endpoint
API_ENDPOINT = 'https://herokuscrapy-8d468df2dace.herokuapp.com/list_files'  # Update with your actual API endpoint URL

def list_files_endpoint():
    # Send a GET request to the API endpoint
    response = requests.get(API_ENDPOINT)

    # Print the response status code
    print(f"Response Status Code: {response.status_code}")

    # Print the response content
    print("Response Content:")
    print(response.json())


def retrieve_file_by_id(file_id : str):
    # Define the base URL of your API
    base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain
    
    # Define the endpoint URL
    endpoint_url = base_url + f"/get_file/{file_id}"  # Update YOUR_FILE_ID with the actual file ID

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

def delete_file_by_id(file_id : str):
    # Define the base URL of your API
    base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain
    
    # Define the endpoint URL
    endpoint_url = base_url + f"/delete_file/{file_id}"  # Update YOUR_FILE_ID with the actual file ID

    try:
        # Make a GET request to the API endpoint
        response = requests.get(endpoint_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the content of the file to the console
            print(response.text)
        else:
            # Print an error message if the request was not successful
            print("Error: Unable to delete file. Status code:", response.status_code)
    
    except requests.RequestException as e:
        # Print an error message if an exception occurs during the request
        print("Error:", e)


base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com/create_file"
def test_create_file_api():
    # Define the API endpoint URL
    api_url = base_url + "/proxies.txt/text"

    try:
        # Open the proxies.txt file and read its content
        with open("proxies.txt", "rb") as file:
            content = file.read()
        
        # Make a POST request to the API endpoint with the file content
        response = requests.post(api_url, data=content)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("File uploaded successfully.")
            print("File ID:", response.text)
        else:
            print("Failed to upload file. Status code:", response.status_code)
            print("Response:", response.text)

    except Exception as e:
        print("An error occurred:", e)

def get_request_and_print_response(base_url):
    try:
        response = requests.get(base_url)
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    #test_list_files_endpoint()
    #test_api()
    #get_request_and_print_response(base_url)
    #list_files_endpoint()
    
    list_files_endpoint()
    test_create_file_api()
    list_files_endpoint()
