import requests


def stream(url):
    r = requests.get(url, stream=True)
    for line in r.iter_lines():
        if line:
            print(line)


def download_file(url, api_key):
    local_filename = url.split('/')[-1]
    headers = {'API-Key': api_key}

    # Make a GET request to the server with stream=True to enable streaming
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()  # Raise HTTPError for bad responses (status code >= 400)

        print("here is the response content : ", response.content)

        # Open a local file in binary write mode to write the streamed content
        with open(local_filename, 'wb') as f:
            # Iterate over the response content in chunks and write each chunk to the file
            for chunk in response.iter_content(chunk_size=8192): 
                if chunk: 
                    f.write(chunk)
                    print("Downloading... : "  , chunk)

    
    print("File downloaded successfully here is the file : ", local_filename)
    return local_filename

url = 'http://localhost:5000/get_final_data'  # Example URL


api_key = 'aqswdefr12345'

headers = {
    'API-Key': api_key
}

#response = requests.get(url, headers=headers)




#print("Status Code:", response.status_code)
#print("response header:  " , response.headers)
#print("Response Body:", response.text)

downloaded_file = download_file(url, api_key)
print(f"File downloaded: {downloaded_file}")

