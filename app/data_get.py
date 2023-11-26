import requests

url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_final_data"
#url = 'http://localhost:5000/get_final_data'  # Example URL


api_key = 'aqswdefr12345'

headers = {
    'API-Key': api_key
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response Body:", response.text)

if response.status_code == 200:
    # Write the response content to an output.xml file
    with open('output.xml', 'w', encoding='utf-8') as file:
        file.write(response.text)
        print("Content written to output.xml")
else:
    print("Failed to fetch data.")