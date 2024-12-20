Overview 
----------------------------------------------------------


GOAL : To get daily up-to-date data about products from the Arukereso website using a Flask application.

This is a flask application.

It runs autonomously the daily task and scrapes the Arukereso website.
Link : https://www.arukereso.hu/
The daily task run can be configured on the server where the projects runs buy hitting
the /get_data (whole category scrape) or /start_url_scrape (for the specific urls) api endpoint.

Or in the main.py file where it looks for the current time and hits itself.

                        +----------------------------------+
                        |          Website Structure       |
                        +----------------------------------+
                                        |
                                        v
        +-------------------+-------------------+-------------------+
        |   Big Category 1  |   Big Category 2  |   Big Category 3  |           Category URL
        +-------------------+-------------------+-------------------+           ============
                    |                   |                   |
                    v                   v                   v
        +----------------+     +----------------+     +----------------+
        |  Product Group |     |  Product Group |     |  Product Group |
        |                |     |                |     |                |          Group URL
        | (Approx. Price)|     | (Approx. Price)|     | (Approx. Price)|        =============
        +----------------+     +----------------+     +----------------+
                    |                   |                   |
                    v                   v                   v
        +-------------------+ +-------------------+ +-------------------+
        | Vendor 1 (Price)  | | Vendor 1 (Price)  | | Vendor 1 (Price)  |
        +-------------------+ +-------------------+ +-------------------+
        | Vendor 2 (Price)  | | Vendor 2 (Price)  | | Vendor 2 (Price)  |
        +-------------------+ +-------------------+ +-------------------+
        | Vendor 3 (Price)  | | Vendor 3 (Price)  | | Vendor 3 (Price)  |
        +-------------------+ +-------------------+ +-------------------+
        


The client can interact through APIs with the server.
The end result is a json file containing : product names, prices, url , category.

The server pushes to google drive automatically the resulting files, 
using the google drive api.

The server is designed that these api endpoint will not be open for public only for 
other servers or front end servers.

Main structure:

                                        +-----------------------+
                                        |   Client Application  |
                                        +----------+------------+
                                                   |
                                                   v
                                        +----------+------------+
                                        |     Flask Server      |
                                        +----------+------------+
                                                   |
                       +---------------------------+---------------------------+
                       |                           |                           |
                       v                           v                           v
            +----------+------------+   +----------+------------+   +----------+------------+
            |  /get_data Endpoint   |   |/start_url_scrape      |   | /get_final_data       |
            |  /start_aprox_scrape  |   | Endpoint              |   | Endpoint              |
            +----------+------------+   +----------+------------+   +----------+------------+
                       |                           |                           |
                       v                           v                           v
            +----------+------------+   +----------+------------+   +----------+------------+
            |     Initiate Scrapy   |   |     Initiate Scrapy   |   |     Retrieve Data     |
            |     Spider for        |   |     Spider for URLs   |   |     from Local        |
            |     Whole Category    |   +-----------------------+   |     Filesystem        |
            +----------+------------+                               +----------+------------+
                       |
                       v
            +----------+------------+
            |  Scrapy Spider Runs   |
            +----------+------------+
                       |
                       v
            +----------+------------+
            | Save Data Locally     |
            | (Filesystem)          |
            +----------+------------+
                       |
                       v
            +----------+------------+
            | Push Data to Google   |
            | Drive (Google Drive   |
            | API)                  |
            +-----------------------+
                       |
                       v
            +----------+------------+
            | Data Available for    |
            | Client Access         |
            +-----------------------+


Documentation structure.

    -> Overview
    -> Usage (API description)
    -> Technical description

Usage:
--------------------------------------------------
API Endpoints:
    # TODO  !! add example usage for each api endpoint !!

    Note: An API key must be provided in the header as a parameter named `shrek_key`. This key is used for internal API calls.
    Named "shrek_key". (Shrek key is used for internal api calls.)

    Return datatype is a json file.

    API endpoints defined in api_manager/api_route.py:

    -> /ping Method: GET**
        Description: Checks if the server is running.

        Request Headers: None
        Request Body: None

        Response:

            -200 OK: Returns JSON with the server status

    -> /check_api_key Method: GET

        Description: Checks if the provided API key is correct.

        Request Headers:

            Authorization (string): shrek_key : "key".
        Request Body: None

        Response:
            -200 OK: Returns JSON if the API key is correct

    -> /run_spider   Method: GET
         Description: Api endpoint to run the spiders.

         Request Headers:

            Authorization (string): shrek_key : "key".

        Request Body: 
            spider_name : str -> The name of the spider that you want to run.
            output_name : str -> The name of the output file.

          Optional
            category : List[str] -> The list of categories that you want to scrape.
                    -> Spider names : "aprox-spider" or "imp-aprox-srape"
                        These are the only spider that can adjust their categories.

            url : List[str] ->The list of url that you want the spider to scrape.
                    -> Spider name: "url-crawl"
                        This is the only spider that can take in url as a parameter.
                        Scrapes only the provided urls.

        If an optional argument was not given for aprox_spider, imp-aprox_spider or url_crawl
        the spider will not run and 404 status code will be given.

        For "arukereso_all" spider the additional arguments are not needed.

        Detailed description about the different spiders are provided below.

        Responses:
            200 Ok : Spider run successfully.
            401 Unauthorized: If the API key is invalid.
            403 Bad request : If there is no spider_name or output_file name provided.
            404 Not Found: Spider dose not exists.
            500 Internal Server Error: If there is an error starting the spider.

        Example Usage:

            TODO  show example usage

    -> /retrive_file Method : GET:
        Description : Api endpoint to retrive files.

        Request Headers:
            Authorization (string): shrek_key : "key".

        
        Request Body:
            file_name : str -> The output file name that was specified in the /run_spider api call.

        Responses:
            200 Ok : Body content is the data streamed.
            401 Unauthorized: If the API key is invalid.
            403 Bad request : If there is no  file name provided.
            404 Not Found: File dose not exists.
            500 Internal Server Error: If there is an error starting the spider.

    API endpoints defined in api_manager/google_drive/google_drive_api_auth.py:
    !Every google drive authentication data must be provided in the server environment variables.

    #TODO !!there are duplicate api endpoint in the google endpoint!!


    -> /list_files METHOD = GET
        Lists the available files in the google drive.

        Request Headers: 
            Authorization (string): shrek_key : "key".   # TODO  no api key needed !!
        Request Body: None

        Possible returns:
            200 :
                {'message': 'No files found'}
                or 
                Json file structured : {name : str, id (google drive file id) : str}
            403 - Incorrect api key
            500 - {'error': 'Authentication failed or an error occurred'}

    -> /get_file/<file_id> METHOD = GET

        Request Headers: 
            Authorization (string): shrek_key : "key".   # TODO  no api key needed !!
        Request Body: None

        Parameter : file_id : str -> Google drive inner file id. Must provide!
        Get the the wanted file id from the /list_files api endpoint.

        When retrieving file even if the file is stored in gzip compression the server returns the uncompressed version.

        Possible returns:
            Directly returns the response from google drive api.
            Uses data streaming. 

            500 : "Error occurred while retrieving the file."

    -> /create_file/<file_name>/<file_mimeType>/<force_update> METHOD = POST
        Uploads a new file in the google drive.

        # TODO  handle cases where the mime type is not defined.

        Request Headers: 
            Authorization (string): shrek_key : "key".   # TODO  no api key needed !!
        Request Body: None

        Parameters:
            - file_name : str - The intended file name - Must provide!
            - file_mimeType : str - The intended file type. Must corresponding to the encoded mime types! - Must provide!
                Possible mime types:
                    - "text"  ->  plain text format.
                    - "ipynb" ->  executable python script.
                    - "csv"   ->  csv file.
                                  Suggestion : use more csv file than txt file for easier data handling.
                    - "gzip"  ->  a compressed gzip file for smaller data amount. 
                                  Suggestion: Use gzip for whole category data storing. 

            - force_update : 0/1 - If wanted to forcefully overwrite the file name even if the file is already exists. - Optional.
                - base value = 0 => no overwrite

        Possible returns:
            - 200 {newly created file id.}
            - 400 {'error': 'File name and MIME type are required.'} or {'error': 'File name already exists.'}
            - 403 {'error': 'Invalid API key'}

    -> /delete_file/<file_id> METHOD = GET
        Deletes an uploaded file from google drive.
        WARNING : There is no confirmation step in deleting the file!

        Request Headers: 
            Authorization (string): shrek_key : "key".   # TODO  no api key needed !!
        Request Body: None

        Parameters:
            -file_name: str - The name of the file to delete. !Must provide!

        Possible returns:
            -403: { "error": "Invalid API key" }
            -200: "File deleted successfully"
            -404: "File not found"
            -500: "An error occurred"

    -> /run_script METHOD = GET
        Runs a Python script from Google Drive.

        Request Headers: 
            Authorization (string): shrek_key : "key".   # TODO  no api key needed !!
        Request Body: None

        Parameters:
            - shrek_key: str - API key in request headers.
            - file_id: str - The ID of the script file to run in request headers.

        Possible returns:
            -200: Script output.
            -400: "Invalid Python code"
            -403: { "error": "Invalid API key" }
            -500: "An error occurred while running the script."

    -> /upload   METHOD  = POST
    -> /download_uploaded/<file_name>   METHOD = GET

  All the api endpoints rely on data_retrieve.py file.
  It manages the run commands for the different spiders.
  It passes the kwargs for the spiders if needed.



There are three big parts of my application.
Components:
-> Main flask server
-> Scraper
    -> Proxy scraper
-> Google Drive communication
    # gzip coding implemented for shorted data amount.

-------------------------------------------------------------
                   The data flow:

            +---------------------------------+
            |       Flask Application         |
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |  API Endpoint Triggered         |
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |    data_retrieve.py             |         Handles API requests and initiates the Scrapy spiders.
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |    Initiate Scrapy Spider       |
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |      Scrapy Spider Runs         |
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |  Save Data Locally (Filesystem) |
            +---------------------------------+
                            |
                            v
            +---------------------------------+
            |  Push Data to Google Drive      |
            +---------------------------------+

------------------------------------------------------------
Main Flask server
------------------------------------------------------------
This is the central server that manages all the components.

main.py
    This is the main entry point for the Flask application.

    Responsibilities:
        API Endpoint Registration: This file is responsible for registering all API endpoints through blueprints, enabling modular and organized route management.

    -> api: Handles core API functionality.
    -> proxy_blueprint: Manages proxy-related requests and operations.
    -> google_drive_api: Interacts with Google Drive for data storage and retrieval.
    -> Daily Job Scheduling: Contains a function that triggers a daily job to scrape data at a specified time (9:00 AM).

    send_request: Sends a GET request to the scraping endpoint to initiate data retrieval.
    -> run_daily_job: Monitors the current time and executes the scraping job daily. It sleeps for a minute between checks to optimize performance.
    How to Run:
        -> The application can be executed by running this file directly, which starts the Flask development server in debug mode.
    Example Usage:
    -> To run the application, execute :  "python main.py" in the terminal. The server will start, and the daily job will be scheduled automatically.


    WARNING : Before running add all the neccessary environment variables!
        ->  Google drive credential 
        -> Shrek key
        -> home url

data_retrieve : SpiderRunner class:
    #  TODO  if there is a spider running with the same name the server crashes!! 
    # TODO spier dose not starts
    Overview
    The SpiderRunner class is designed to facilitate the running of Scrapy spiders from a Python script.
    It allows for dynamic configuration of the spider's parameters,
    making it flexible and easy to use in various contexts, such as within an API endpoint.
        
    Example usage:
        spider_runner = SpiderRunner(
        spider_name='aprox-spider',
        output_file='outputUrl.json',
        category='electronics'
                                    )
        spider_runner.run()
    Callable functions:
        run() : runs the spider declared in the constructor.
            return values:
                0 - Run was successful
                -1 - Spider dose not exists.
                1 - Spider did not run successfully.
    Only callable function is the run() it  above.

    Additional functions:
        _run_spider(): (private) : Task is to run the crawl spider command in the correct dictionary.
        _spider_exists() : (private) : Task is to check if the spider that is constructed exists.

------------------------------------------------------------
Scrapy
------------------------------------------------------------
This part is responsible for running the main scraping part.
It contains multiple spiders for different tasks.

! To setting.py I put close item count 10 for testing purposes ! 

Location: app\heroku_scrapy\heroku_scrapy\spiders

                        Main scraping methods


        +-----------------------------+------------------------------------------------+
        | Whole Website Scraping                                                       |
        +-----------------------------+------------------------------------------------+
        | Description                 | Scrapes the entire website, capturing all      |
        |                             | accessible pages.                              |
        +-----------------------------+------------------------------------------------+
        | Benefits                    | - Comprehensive data collection                |
        |                             | - Ensures no relevant data is missed           |
        +-----------------------------+------------------------------------------------+
        | Drawbacks                   | - Higher resource consumption                  |
        |                             | - Increased processing time                    |
        |                             | - Cannot retrieve the json while running        |
        +-----------------------------+------------------------------------------------+

        +-----------------------------+------------------------------------------------+
        | External Source URLs                                                         |
        +-----------------------------+------------------------------------------------+
        | Description                 | Fetches URLs from an external source and       |
        |                             | scrapes only the provided URLs.                |
        +-----------------------------+------------------------------------------------+
        | Benefits                    | - Targeted data collection                     |
        |                             | - Lower resource consumption                   |
        +-----------------------------+------------------------------------------------+
        | Drawbacks                   | - Potentially misses relevant data not listed  |
        |                             | - Depends on the accuracy of the provided URLs |
        +-----------------------------+------------------------------------------------+

        The different api calls are responsible for witch method is used.


                          Preferred scraping usage
                        +-------------------------+
                        | Scrape the whole website|
                        |   once a week to capture|
                        |   all new products or   |
                        |   URL changes           |
                        +-------------------------+
                                    |
                                    v
                        +-------------------------+
                        |  Scrape the URLs only   |
                        |        daily            |
                        +-------------------------+
                                                    
#TODO  write the exact api endpoint for this scenario.

All scraping methods implement user agent header rotations and proxy rotation.
User agent headers are stored in a txt file.

Proxies are got from a third party website.
Link : https://free-proxy-list.net
 

For every request a different proxy and user agent is used.
If a proxy is still alive it may be used multiple times.

If a proxy is not alive it is deleted from the proxy pool.
Before and during scarping process the proxies are tested and refreshed asynchronously.

Spider 

url_crawl:

                +---------------------------------+
                |        URL Scrape API           |
                |  /start_url_scrape is triggered |
                |         Endpoint Triggered      |
                +---------------------------------+
                                |
                                v
                +---------------------------------+
                |    run_url_scrape Function      |
                |    Triggered in data_retrieve.py|
                +---------------------------------+
                                |
                                v
                +---------------------------------+
                |         Command is Run          |
                |  I gets the url list from the   |
                |  api endpoint                   |
                +---------------------------------+
                                |
                                v
                +---------------------------------+
                |     URL Scrape Spider Runs      |
                +---------------------------------+

arukereso_all:

    
    # TODO multiple check proxy status functions 
    #  -> There is a proxy check outside of the class and there is a inner check proxy 
    # TODO  -> make an proxy manager class that strores and return only a proxy that is needed 
    # TODO      -> Add the proxy checker to that class a function 
    # TODO      -> Add select proxy 

                +----------------------------+
                |       Spider Starts        |
                +----------------------------+
                            |
                            v
                +----------------------------+
                |    User Agent Reading      |
                +----------------------------+
                            |
                            v
                +----------------------------+
                |     Proxy Gathering        |
                +----------------------------+
                            |
                            v
                +----------------------------+
                |      Proxy Testing         |
                +----------------------------+
                            |
                            v
                +----------------------------+
                |  Main Scraping Process     |
                +----------------------------+
                            |
                            v
                +----------------------------+
                | Proxies Available?         |
                |   Yes        |    No       |
                +----------------------------+
                |     |                      |
                |     v                      |
                | Continue                   |
                |     |         |            |
                |     |         v            |
                |     |   +-----------------+|
                |     |   | Proxy Gathering ||
                |     |   +-----------------+|
                |     |         |            |
                |     |         v            |
                |     |   +-----------------+|
                |     |   |  Proxy Testing  ||
                |     |   +-----------------+|
                |     |         |            |
                |     v         v            |
                | +-------------------------+|
                | Main Scraping Process      |
                | +-------------------------+|
                +----------------------------+

    Proxy scraping is made from a third party free api.
    URL : https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=no&anonymity=elite

    The gathering and testing process runs sumiltaniusly with the main scraping process.

    aprox_spider

    Overview
        The AproxSpiderSpider is a Scrapy spider designed to scrape product data from specific categories on the Arukereso website. 
        It generates URLs dynamically based on a prediction model to collect comprehensive product information,
        including names, prices, and comparison links.

        The spevific category to crawl is added from the api call as POST method.

        # TODO  finish the category slection in the spider!

    Spider is written for testing purposes.

    Item Limit
        The spider is configured to stop scraping for a URL after collecting 25 "blue products."

    There is an improved version of this spider the imp-aprox-srape. 
    It dose not generates the urls but follows them it finds on the website.
    Can handle if the url structure changes.

    Use the imp-aprox-srape!! 

    ProxyManager class:
        Task : Manage and handle  proxies for use.
            Gets proxies from and api. 
            Link : https://api.proxyscrape.com

        Returns with a proxy. If the proxy is not working delete it than ask for a new one.

        Public functions:
            get_proxy -> No param -> returns with a proxy(string) 

            delete_proxy -> Param : proxy(string) -> Deletes the given proxy and if the length of the proxy list is 0 gets a nw list.

            get_useragent -> No param ->Returns a list of string. User agents for requests.
            I placed this function here so that the scrapie code can be clean.

        Private Functions
            _get_new_proxy_list -> No param -> returns with proxy list from the api.

            _check_proxy_status -> Param : Proxy(string), test url(string) -> Bool True if the proxy is alive.
            (Not used)

            _check_proxy_list -> Param : test_url (string) -> Return with a valid proxy list.
            (Not used)

            I choose not use these function because they slow down the process of scraping substantially.
            While waiting for each response to happen it can take over 300 seconds if you make the proxy checking multithreaded and asynchronously.
            And 300 seconds adds up.
        



------------------------------------------------------------
Google Drive API
------------------------------------------------------------
    This part is responsible for reading, writing, deleting and creating files to Google Drive.
    Storing data on Google drive is easy and free for a set of data.up to 15 GB.
    ->Thats why i choose to store data in gzip format.

    Google Documentation : https://developers.google.com/drive/api/quickstart/python

    Location : app/api_manager/google_drive

    -> google_drive_api_auth.py
        This part is responsible for authentication for each api call to Google Drive.

        It uses server environment variable.

    -> google_adrive_apiendpoint.py
        Here is defined all the different operation that can be made to Google drive api.

Security:
    # TODO  store the shrek key in hashed format
    # TODO should i implement api key rotation or renewal?
    # TODO  rate limiting 
    # TODO ip cheking and logging for api calls.
    # TODO add api checking logic ! 

    The api keys are stored on the server side as system variables.

Logging:
    # TODO  should i implement log files?


Performance:
    # TODO create benchmark files that showcase different scenarios.

    Server is using asynchronously and multithreading for boosting performance.


Necessary environment variables:
     -> "home_url" : str 
        The servers ip where the server is running.
        Like : "home_url" : "htttp://something.com"
        
     -> "valid_api_keys" : dict
        The dictionary of api_keys that can make http cal to this server.
        Like: valid_api_keys = {
            "12345" : True,
            "1234567" : False,
                                }

     -> "shrek_api_key" : str
        I used shrek key as the main key to communicate between my other servers.

        Like : "shrek_api_key" : "qwertzuiop"


    Google Drive credetials needed: 
        -> "google_drive_api_type"
        -> "google_adrive_api_project_id"
        -> "google_drive_api_private_key_id"
        -> "google_drive_api_private_key"
        -> "google_drive_api_client_email"
        -> "google_drive_api_client_id"
        -> "google_drive_api_auth_uri"
        -> "google_drive_api_token_uri"
        -> "auth_provider_x50 "google_drive_api_auth_provider_x509_cert_url"
        -> "google_drive_api_client_x509_cert_url"
        -> SCOPES
    
