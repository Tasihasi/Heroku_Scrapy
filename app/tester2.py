import requests

url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_final_data"
#url = 'http://localhost:5000/get_final_data'  # Example URL


api_key = 'aqswdefr12345'

headers = {
    'API-Key': api_key
}

response = requests.get(url, headers=headers)

"""
i = 0 
while "Data is not yet available. Please try again later." in response.text or i == 100:
    i+=1
    response = requests.get(url, headers=headers)
    print(i)
"""

print("Status Code:", response.status_code)
print("Response Body:", response.text)