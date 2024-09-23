# Returns user agent 
#manages the proxy scraping proccess 
# Tests the proxies 
# function that retruns a random proxy 

# TODO write test before developing

import requests
from typing import List
from concurrent.futures import ThreadPoolExecutor



class ProxyHandler:
    

    

    def get_new_proxy(self):
        # Implement logic to return a proxy
        raise NotImplementedError
    

    # Test if the proxy is alive 5 times
    def check_proxy_status(self, proxy : str , test_url : str) -> int:
        test_url = "https://www.arukereso.hu/nyomtato-patron-toner-c3138/"

        try:
            if requests.get(proxy, timeout=5).status_code != 200:

                # TODO implement port scan
                # TODO REplace the port with the working port

                return -1


            response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=3)
            if response.status_code == 200:
                return int(proxy.split(":")[-1]) # ?? why ? why not 1?
            
            
            return -1

        except requests.RequestException:
            raise requests.RequestException

    
    def get_new_raw_proxy(self) -> List[str]:
        try:
            response = requests.get(url)

            if response.status_code == 200:
                # Successful response
                proxies = response.text.strip().split("\n")
                proxies = [f"http://{proxy.strip()}" for proxy in proxies]
                return check_proxy_multi_threadedly(proxies)
            else:
                # Handle other status codes if needed
                pass
                #print(f"Request failed with status code: {response.status_code}")

        except requests.RequestException as e:
            # Handle exceptions or errors
            pass
            #print(f"An error occurred: {e}")


    def check_proxy_multi_threadedly(self, proxies : List[str], test_url : str) -> List[str]:
        """
        Check if a proxy is working by making a request to a test URL.
        """

        def check_and_format_proxy(proxy):
            if -1 < check_proxy_status(proxy, test_url):
                return proxy
            return None
        

        valid_proxies = List[str]

        with ThreadPoolExecutor(max_workers=200) as executor:
            results = executor.map(check_and_format_proxy, proxies)

        # Filter out None values and return the list of valid proxies
        valid_proxies = [proxy for proxy in results if proxy is not None]

        return valid_proxies
