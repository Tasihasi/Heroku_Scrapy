import requests, random
from typing import List



class ProxyHandler:
    def __init__(self) -> None:
        self.proxy_list = self._get_new_proxy_list()

    # Returns with a list of proxies.
    def _get_new_proxy_list(self):
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=no&anonymity=elite"

        try:
            response = requests.get(url)

            if response.status_code == 200:
                proxies = response.text.strip().split("\n")
                proxies = [f"http://{proxy.strip()}" for proxy in proxies]

                return proxies
            else:
                return False

        except requests.RequestException as e:
            return False

    # Test if the proxy is alive 5 times
    def _check_proxy_status(self, proxy : str , test_url : str) -> bool:
        try:
            response = requests.get(test_url, proxies={"http://": proxy}, timeout=3)

            if response.status_code != 200:
                return True

            return False

        except requests.RequestException:
            return False

    # Returns a valid proxy list
    def _check_proxy_list (self, test_url : str) -> List[str]:
        valid_proxies = List[str]

        raise NotImplementedError
        return valid_proxies

    # The user can get a new proxy from this 
    def get_proxy(self) -> str:
        return random.choice(self.proxy_list)
    
    # Deletes the given proxy and if the length of the proxy list is 0 than gets a new proxy list
    def delete_proxy(self, proxy : str) -> None:
        self.proxy_list.remove(proxy)

        if len(self.proxy_list) == 0:
            self.proxy_list = self._get_new_proxy_list()

    #Returns user agent
    def get_user_agents(self) -> List[str]:
        with open('useragents.txt') as f:
            USER_AGENT_PARTS = f.readlines()
        return USER_AGENT_PARTS



