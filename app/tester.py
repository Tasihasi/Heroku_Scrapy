import requests

url = 'https://herokuscrapy.herokuapp.com/get_data'
response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
