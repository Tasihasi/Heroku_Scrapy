import os
import logging
from .api_proxy import wait_for_file, delete_existing_file, run_spider

# Import necessary components
from nbconvert import NotebookExporter, PDFExporter
from nbformat import read
from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
import logging

import os


# Define the path to your notebook file



def run_notebook(path : str, notebook_name : str) -> None:

        # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the notebook
    notebook_path = os.path.join(script_dir, notebook_name)

    print(f"Notebook path: {notebook_path}")

    # Load the notebook
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    # Create an instance of ExecutePreprocessor
    execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name='python3')

    # Execute the notebook
    execute_preprocessor.preprocess(nb, {'metadata': {'path': script_dir}})

def check_dependencies(path : str, notebook_name : str) -> bool:
    # Check if the necessary components are installed
    def check_file_exists(file_path: str) -> bool:
        # Check if the file exists
        if os.path.exists(file_path):
            logging.info(f"The file {file_path} exists.")
            return True
        else:
            logging.error(f"The file {file_path} does not exist.")
            return False

    file_paths = [
        notebook_name,
        "customer_request.json",
        "output.jsonl",
    ]

    for file_path in file_paths:
        if not check_file_exists(path +file_path):
            logging.error(f"The file {path + file_path} does not exist.")
            return False
        
    return True


# Input : path to the directory containing the necessary files
def run_data_man(path : str) -> bool:
    #print("Current working directory:", os.getcwd())

    # Get the list of all files and directories in the current working directory
    #file_list = os.listdir(os.getcwd())

    #print("Files and directories in '", os.getcwd(), "':")
    # Print the list
    #for file in file_list:
        #print(file)

    # Check if the necessary files are present

    notebook_filename = 'get_matching_data.ipynb'

    try:
        if check_dependencies(path, notebook_filename):
            print("All necessary files are present.")
            try :
                print("Running the notebook.")
                # Run the notebook
                run_notebook(path, notebook_filename)
                return True
            except Exception as e:
                print(f"An error in the run_notebook: {e}")
                logging.error(f"An error in the run_notebook: {e}")
                return False
        else:
            print("Necessary files are not present.  Please ensure that the necessary files are present.")
            logging.error("Necessary files are not present.  Please ensure that the necessary files are present.")

    except Exception as e:
        print(f"An error occurred in the file checking: {e}")
        logging.error(f"An error occurred in the file checking: {e}")
        return False

def get_top_5_products(path : str) -> bool:


    notebook_name = 'get_top_5_products.ipynb'
    try:
        if check_dependencies(path, notebook_name):
            print("All necessary files are present.")
            try :
                print("Running the notebook.")
                # Run the notebook
                run_notebook(path, notebook_name)
                return True
            except Exception as e:
                print(f"An error in the run_notebook: {e}")
                logging.error(f"An error in the run_notebook: {e}")
                return False
        else:
            print("Necessary files are not present.  Please ensure that the necessary files are present.")
            logging.error("Necessary files are not present.  Please ensure that the necessary files are present.")

    except Exception as e:
        print(f"An error occurred in the file checking: {e}")
        logging.error(f"An error occurred in the file checking: {e}")
        return False






logging.basicConfig(level=logging.DEBUG)
def get_data_from_scrapy():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    print(f"Script Directory: {script_dir}")

    logging.info(f"Script Directory: {script_dir}")

     # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'arukereso_all', '-O', 'Result.json']

    logging.info("Running spider  the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        logging.info("not running spider")
        return
    
    logging.info("Theoreticly spider runs")


def get_proxies():
    # Get the current directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the relative path to the Scrapy spider directory
    spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
    print(f"Script Directory: {script_dir}")

    logging.info(f"Script Directory: {script_dir}")

     # Change the working directory to the spider directory
    os.chdir(spider_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the Scrapy command
    command = ['scrapy', 'crawl', 'free_proxy_list' , '-O', 'Result.xml']

    logging.info("Running spiderin the data_retrive.py")

    # Step 2: Run the spider
    if not run_spider(command):
        return



def main():
    run_data_man("")


if __name__ == '__main__':
    main()