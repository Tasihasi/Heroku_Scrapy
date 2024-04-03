from flask import Flask
from .api_manager.api_route import api, proxy_blueprint
from .api_manager.google_drive.google_adrive_apiendpoint import google_drive_api
import requests
import time
from datetime import datetime, timedelta
from daemonize import Daemonize


def send_request():
    url = "https://herokuscrapy-8d468df2dace.herokuapp.com/get_data"

    response = requests.get(url)

    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

def run_daily_job():
    # Set the target time for the daily job (9:00 AM)
    target_time = datetime.combine(datetime.today(), datetime.min.time()) + timedelta(hours=9)

    while True:
        # Calculate the time until the target time
        current_time = datetime.now()
        time_diff = (target_time - current_time).total_seconds()

        if time_diff <= 0:
            # If current time is past the target time, execute the job
            send_request()
            # Schedule the next run for the next day
            target_time += timedelta(days=1)
        else:
            # Sleep until the next check (every minute in this case)
            time.sleep(60)



app = Flask(__name__)

print("Started the app")

# Register the API blueprint
app.register_blueprint(api)  # Register the 'api' Blueprint
print("imported the api blueprint printed with print")

app.register_blueprint(proxy_blueprint)
print("imported the proxy blueprint printed with print")

app.register_blueprint(google_drive_api)

app.run(debug=False, threaded=True  , port=5000)
print("Started the app")

# Define a main function to run the app
def main():
    # Create a Flask application instance
    

    #
    app.run(debug=True, threaded=True  , port=5000)

if __name__ == '__main__':
    #daemon = Daemonize(app="my_app", pid="/tmp/my_app.pid", action=main)
    #aemon.start()
    pass
