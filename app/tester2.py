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