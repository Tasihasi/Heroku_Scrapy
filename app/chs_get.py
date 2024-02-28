import requests

url = 'http://ppgateway.new.on-demand.hu/v1/datacollector/compmarket?apikey=a5e3fTzJJcOU2DEevspm3RYTJP0OMG3s'


response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Body:", response.text)



