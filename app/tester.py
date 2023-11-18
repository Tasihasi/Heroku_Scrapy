import requests

url = 'https://herokuscrapy.herokuapp.com/get_data'
url = "https://herokuscrapy-8d468df2dace.herokuapp.com/ping"
response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
