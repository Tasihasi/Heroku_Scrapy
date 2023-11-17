import os

# Get the directory containing the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Relative path to the JSON file from the script's directory
relative_path_to_json = os.path.join(script_directory, '..\scrapy\proxy_manager\proxy_scraper\proxy_ips.json')

# Convert to an absolute path
absolute_path_to_json = os.path.abspath(relative_path_to_json)

def is_json_file_exist(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False

print("Checking for file at:", absolute_path_to_json)
if is_json_file_exist(absolute_path_to_json):
    print("JSON file exists.")
else:
    print("JSON file does not exist.")
