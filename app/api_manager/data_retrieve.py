import subprocess, logging, os, psutil
from flask import Response, jsonify, stream_with_context


class SpiderRunner:
    def __init__(self, spider_name : str, output_file : str, *args, **kwargs):
        self.spider_name = spider_name
        self.output_file = output_file
        self.args = args
        self.kwargs = kwargs

    def _run_spider(self, command : str):
        try:
            # Use subprocess.Popen to run the spider in the background
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logging.info(f"Started spider {self.spider_name} with PID {process.pid}")
            
            return True, process
        except subprocess.CalledProcessError as e:
            print("Failed to run the spider:", e)
            return False, None

    def _spider_exists(self) -> bool:
        """Check if the specified spider exists."""
        command = ['scrapy', 'list']
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
            available_spiders = result.stdout.splitlines()
            return self.spider_name in available_spiders
        except subprocess.CalledProcessError as e:
            print("Failed to list spiders:", e)
            return False
        
    def _correct_spider_arguments(self) -> bool:
        if type(self.spider_name) != str or type(self.output_file) != str:
            return False
        elif "urls" not in self.kwargs and (self.spider_name == "aprox-spider" or self.spider_name == "imp-aprox-spider"):
            return False
        
        elif "category" not in self.kwargs and self.spider_name == "url-crawl":
            return False
        
        return True

    def _is_spider_running(self) -> bool:
        """Check if a spider with the same name is currently running."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'scrapy' in proc.info['cmdline'] and self.spider_name in proc.info['cmdline']:
                logging.info(f"Spider {self.spider_name} is already running with PID {proc.info['pid']}")
                return True
        return False

    def run(self) -> int:
            if not self._correct_spider_arguments():
                return 0

            script_dir = os.path.dirname(os.path.abspath(__file__))
            spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
            os.chdir(spider_dir)
            print(f"Changed working directory to: {os.getcwd()}")

            # Check if the specified spider exists
            if not self._spider_exists():
                logging.error(f"Spider '{self.spider_name}' does not exist.")
                print(f"Error: Spider '{self.spider_name}' does not exist.")
                return -1

            command = ['scrapy', 'crawl', self.spider_name, '-O', self.output_file]

            # Add any positional arguments to the command
            for arg in self.args:
                command.append(arg)

            # Add any keyword arguments to the command
            for key, value in self.kwargs.items():
                command.extend([f'-a', f'{key}={value}'])

            # TODO Check if there is a same named spider running in the background

            logging.info(f"Running spider {self.spider_name} with output {self.output_file}")
            if not self._run_spider(command):
                logging.info("Spider did not run successfully")
                return 0
            logging.info("Theoretically, the spider runs")

            return 1
    

class RetriveData():
    def __init__(self, output_file_name : str):
        self.output_file_name = output_file_name

    
    def _generate_file_path(self) -> str:
        app_root = os.path.abspath(os.path.dirname(__file__))
        directory = "../heroku_scrapy"
        folder_log = os.path.join(app_root, directory)

        
        json_path = os.path.join(folder_log, self.output_file_name)
        return json_path

    def _is_file_exists(self, path:str) -> bool:
        if len(path) == 0 or not os.path.exists(path):
            return False
        
        return True
    
    # Function to stream JSON data from file
    def _generate(self, path : str):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                yield line.rstrip() + '\n'

    def get_file(self, path : str):
        ful_path = self._generate_file_path(self.output_file_name)

        if not self._is_file_exists(path):
            logging.error(f"File not found: {path}")
            return jsonify({"error": "File not found"}), 404

        # Return the streamed response
        return Response(stream_with_context(self._generate(path)), content_type='application/json')


if __name__ == '__main__':
    pass