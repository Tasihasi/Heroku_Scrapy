import requests
import json


api_key = "B1FL2WGYdCJN1a6MCTKTRg8PHCYEiuaQQSS1A1Ad8k44"


url = "https://api.proxifly.dev/get-proxy"

# Define the parameters for the request
params = {
    "countries": ["US", "RU"],
    "protocol": ["http", "socks4"],
    "quantity": 2000,
    "https": True
}

# Make the request
response = requests.get(url, params=params, headers={"Authorization": f"Bearer {api_key}"})

# Parse the response
proxies = response.json()

# Print the proxies
print(json.dumps(proxies, indent=4))