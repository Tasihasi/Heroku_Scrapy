import requests

url = 'http://localhost:5000/get_data'  # Example URL


response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Body:", response.text)


