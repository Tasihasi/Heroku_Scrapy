import requests

url = 'https://herokuscrapy.herokuapp.com/get_data'
url = "https://www.arukereso.hu/nyomtato-patron-toner-c3138/?start=30625"
url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_data"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}

response = requests.get(url )#, headers = headers)

print("Status Code:", response.status_code)
print("Response Body:", response.text)



