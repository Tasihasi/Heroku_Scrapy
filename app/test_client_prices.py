import requests

def test_business_logic(api_endpoint : str) -> str:

    shrek_key  = "g96#NjLc}wJR=C~/F7?k2$.,5TDumGEW@s)^M38K](t<;y>[r%"
    # URL of the API endpoint
    api_url = "https://herokuscrapy-8d468df2dace.herokuapp.com/" + api_endpoint

    print(f"API URL: {api_url}")

    # Assuming you have a running local server on port 5000
    # and customer_data.json is accessible via a URL or as a file path the API can access
    
    # Header to be sent in the request
    header = {
        'shrek_key': shrek_key,  # Replace with your actual API key
        #'product_data': 'customer_request.json'  # Replace with the actual path or URL to customer_data.json
    }
    
    # Sending GET request
    response = requests.get(api_url, headers=header)
    
    # Asserting the response status code to check if the request was successful
    return response.status_code
    
    # Further assertions can be added here based on the expected response content


def test_data_retrieval(api_endpoint : str) -> bool:
    # URL of the API endpoint
    api_url = "https://herokuscrapy-8d468df2dace.herokuapp.com/" + api_endpoint

    print(f"API URL: {api_url}")

    # Assuming you have a running local server on port 5000
    # and customer_data.json is accessible via a URL or as a file path the API can access
    
    # Header to be sent in the request
    header = {
        'shrek_key': 'g96#NjLc}wJR=C~/F7?k2$.,5TDumGEW@s)^M38K](t<;y>[r%',  # Replace with your actual API key
    }
    
    # Sending GET request
    response = requests.get(api_url, headers=header)
    
    # Testing if get file in response
    
    print(f"The content of the response is: {response.content}")
    
    return response.content
    


def main():
    # Test the business logic of the API
    #status_code = test_business_logic("customer_data_process")
    
    #print(f"processing data status code: {status_code}")

    # Test data retrieval 
    #status_code = test_data_retrieval("get_business_logic_data")

    #print(f"retrieving data status code: {status_code}")


    #print("Tests completed.")


    #api_url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_top_5_products"

    print(" ----------   running main -------")

    url = "http://127.0.0.1:5000/start_url_scrape"

    print(f"------------ Here is the url : {url} ---------------------- ")

    header = {
        #'shrek_key': 'g96#NjLc}wJR=C~/F7?k2$.,5TDumGEW@s)^M38K](t<;y>[r%',  # Replace with your actual API key
    }

    # Define the payload with the URLs you want to scrape
    payload = {
        "urls": [
            "https://www.arukereso.hu/nyomtato-patron-toner-c3138/canon/pg-545xl-black-bs8286b001aa-p197948661/",
            "https://www.arukereso.hu/nyomtato-patron-toner-c3138/canon/pg-545-cl-546-multipack-8287b005aa-p197943649/",
            "https://www.arukereso.hu/nyomtato-patron-toner-c3138/hp/3ym61ae-p635260836/"
        ]
    }

    response = requests.get(url, headers=header, json=payload)

    print(response.status_code)
    print(response.content)
    

if __name__ == '__main__':
    main()