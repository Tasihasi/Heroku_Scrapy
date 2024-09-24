import requests, json

url = 'http://localhost:5000/run_spider'  # Example URL

header = {"shrek_key" : "12345",
          "Content-Type": "application/json"}
data = {"spider_name" : "arukereso_all" , "output_name" : "Resulting_data.json"}
json_data = json.dumps(data)
response = requests.get(url, data=json_data, headers=header)

print("Status Code:", response.status_code)
print("Response Body:", response.text)


