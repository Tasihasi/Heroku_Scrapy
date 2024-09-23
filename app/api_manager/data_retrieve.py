import subprocess, logging, os

class SpiderRunner:
    def __init__(self, spider_name, output_file, *args, **kwargs):
        self.spider_name = spider_name
        self.output_file = output_file
        self.args = args
        self.kwargs = kwargs

    def run_spider(self, command):
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
            spider_log = result.stdout
            print("Spider Log:")
            logging.info("--------  Spider log : ")
            logging.info(spider_log)
            print(spider_log)
            print("Spider Run in the api_proxy.py")
            return True, spider_log
        except subprocess.CalledProcessError as e:
            print("Failed to run the spider:", e)
            return False, None

    def run(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spider_dir = os.path.join(script_dir, '..', 'heroku_scrapy')
        os.chdir(spider_dir)
        print(f"Changed working directory to: {os.getcwd()}")

        command = ['scrapy', 'crawl', self.spider_name, '-O', self.output_file]

        # Add any positional arguments to the command
        for arg in self.args:
            command.append(arg)

        # Add any keyword arguments to the command
        for key, value in self.kwargs.items():
            command.extend([f'-a', f'{key}={value}'])

        logging.info(f"Running spider {self.spider_name} with output {self.output_file}")
        if not self.run_spider(command):
            logging.info("Spider did not run successfully")
            return
        logging.info("Theoretically, the spider runs")


if __name__ == '__main__':
    pass