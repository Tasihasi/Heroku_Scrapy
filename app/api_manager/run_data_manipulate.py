# Import necessary components
from nbconvert import NotebookExporter, PDFExporter
from nbformat import read
from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
import logging

import os


# Define the path to your notebook file
notebook_filename = 'get_matching_data.ipynb'


def run_notebook(path : str) -> None:

        # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the notebook
    notebook_path = os.path.join(script_dir, notebook_filename)

    print(f"Notebook path: {notebook_path}")

    # Load the notebook
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    # Create an instance of ExecutePreprocessor
    execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name='python3')

    # Execute the notebook
    execute_preprocessor.preprocess(nb, {'metadata': {'path': script_dir}})

def check_dependencies(path : str) -> bool:
    # Check if the necessary components are installed
    def check_file_exists(file_path: str) -> bool:
        # Check if the file exists
        if os.path.exists(file_path):
            print(f"The file {file_path} exists.")
            return True
        else:
            print(f"The file {file_path} does not exist.")
            return False

    file_paths = [
        notebook_filename,
        "customer_request.json",
        "Result.json",
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

    try:
        if check_dependencies(path):
            print("All necessary files are present.")
            try :
                print("Running the notebook.")
                # Run the notebook
                run_notebook(path)
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

def main():
    run_data_man("")


if __name__ == '__main__':
    main()
    
