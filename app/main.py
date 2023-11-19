from flask import Flask
from .api_manager.api_route import api, proxy_blueprint


# Create a Flask application instance
app = Flask(__name__)

# Register the API blueprint
app.register_blueprint(api)  # Register the 'api' Blueprint

app.register_blueprint(proxy_blueprint)

# Define a route and view function
@app.route('/')
def hello_world():
    return 'Hello, World!'



# Define a main function to run the app
if __name__ == '__main__':
    app.run()


