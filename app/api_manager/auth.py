



valid_api_keys = {
    "12345" : True,
    "1234567" : False,
}

api_keys_to_customers ={
    "12345" : "Bela",
}


def is_valid_api_key(apiKey : str) -> bool:
    if apiKey in valid_api_keys:
        return True
    return False

def mach_apiKey_to_customer(apiKey: str) -> str:
    if is_valid_api_key(apiKey):
        return api_keys_to_customers[apiKey]
    else:
        return ""
    
def getting_raw_data(apikey):
    if is_valid_api_key(apikey) and valid_api_keys[apikey]:
        return True
    return False

