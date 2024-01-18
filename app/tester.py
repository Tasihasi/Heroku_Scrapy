import requests

url = 'https://herokuscrapy.herokuapp.com/get_data'
url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_data"
#url = "https://www.arukereso.hu/nyomtato-patron-toner-c3138/?start=30625"
url = 'http://localhost:5000/get_data'  # Example URL

response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Body:", response.text)



