import requests

def get_proxies():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Successful response
            return response.text  # Return the response content
        else:
            # Handle other status codes if needed
            print(f"Request failed with status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        # Handle exceptions or errors
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    proxies = get_proxies()
    if proxies:
        print("Proxies:")
        print(proxies)
