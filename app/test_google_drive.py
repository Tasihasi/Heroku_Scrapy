import requests
import json
import os

shrek_key  = "g96#NjLc}wJR=C~/F7?k2$.,5TDumGEW@s)^M38K](t<;y>[r%"

# URL of your Flask API endpoint
API_ENDPOINT = 'https://herokuscrapy-8d468df2dace.herokuapp.com/list_files'  # Update with your actual API endpoint URL

def list_files_endpoint():

    headers = {"shrek_key": shrek_key}


    # Send a GET request to the API endpoint
    response = requests.get(API_ENDPOINT, headers=headers)

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
        response = requests.get(endpoint_url, timeout=120)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print(f"here is the response : {response.content}")
            print(f"here is the response : {response.__dict__}")

            # Define the chunk size
            chunk_size = 1024  # You can adjust this value depending on your needs
            
            # Iterate over the response data in chunks
            for chunk in response.iter_content(chunk_size):
                # Print the chunk to the console
                print(chunk)
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

        headers = {"shrek_key": shrek_key}
        response = requests.get(endpoint_url, headers=headers)
        
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
def create_file_api():
    # Define the API endpoint URL
    api_url = base_url + "/proba.ipynb/ipynb"

    try:
        # Open the proxies.txt file and read its content
        with open("proxies.txt", "rb") as file:
            content = file.read()
        

        headers = {"shrek_key": shrek_key}
        # Make a POST request to the API endpoint with the file content
        response = requests.post(api_url, data=content, headers= headers)
        
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

def run_coolab_code(file_id : str):
    # Define the base URL of your API
    
    base_url = f"https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain
    
    # Define the endpoint URL
    endpoint_url = base_url + f"/run_script"  # Update YOUR_FILE_ID with the actual file ID

    try:
        # Make a GET request to the API endpoint
        headers = {"shrek_key": shrek_key, "file_id": file_id}
        response = requests.get(endpoint_url, headers= headers)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the content of the file to the console
            print(response.text)
        else:
            # Print an error message if the request was not successful
            print("Error: Unable to run script. Status code:", response.status_code)
    
    except requests.RequestException as e:
        # Print an error message if an exception occurs during the request
        print("Error:", e)


def test_file_upload(file_path : str):
     # Define the base URL of your API
    
    base_url = f"https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain

    # Define the endpoint URL
    endpoint_url = base_url + f"/upload"  

    headers = {"shrek_key": shrek_key}

    files = {'file': open(file_path, 'rb')}
    response = requests.post(endpoint_url, files=files, headers=headers)
    print(response.text)

    # Check the status of the request
    if response.status_code == 200:
        print("File uploaded successfully.")
    else:
        print(f"Failed to upload the file. Status code: {response.status_code}")


def test_my_api_key():
    # Define the base URL of your API
    base_url = "https://herokuscrapy-8d468df2dace.herokuapp.com"  # Update this with your actual API domain
    
    # Define the endpoint URL
    endpoint_url = base_url + "/shrek_key_checker"  # Pass the API key as a query parameter
    
    headers = {"shrek_key": shrek_key}

    response = requests.get(endpoint_url, headers=headers)

    print(response.text)
    print(response.status_code)

if __name__ == "__main__":

    delete_file_by_id("1k0pGqUSTSC_cVQ79K7Ucucg49N_ub_On")
    #create_file_api()

    #run_coolab_code("1k0pGqUSTSC_cVQ79K7Ucucg49N_ub_On")

    #test_my_api_key()

    #create_file_api()
    #list_files_endpoint()
    list_files_endpoint()
    #retrieve_file_by_id("1F4D-A0OOTEP91ArgMYohEbbOpHKsgWT3")

    #test_file_upload("proxies.txt")
