import pytest
from app.main import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_run_spider_valid_request(client):
    response = client.get('/run_spider', 
                            headers={'shrek_key': '12345'}, 
                            json={
                                "spider_name": "arukereso_all",
                                "output_name": "outputUrl.json",
                            })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Spider runs successfully spider name: arukereso_all, output_name: outputUrl.json"

def test_run_spider_invalid_api_key(client):
    response = client.get('/run_spider', 
                            headers={'shrek_key': 'invalid_key'}, 
                            json={
                                "spider_name": "aprox-spider",
                                "output_name": "outputUrl.json"
                            })
    
    assert response.status_code == 401  # Assuming this is the status code you return for invalid API keys

def test_run_spider_missing_spider_name(client):
    response = client.get('/run_spider', 
                            headers={'shrek_key': '12345'}, 
                            json={
                                "output_name": "outputUrl.json"
                            })
    
    assert response.status_code == 403
    data = response.get_json()
    assert data["message"] == "No provided spider name"

def test_run_spider_missing_output_name(client):
    response = client.get('/run_spider', 
                            headers={'shrek_key': '12345'}, 
                            json={
                                "spider_name": "aprox-spider"
                            })
    
    assert response.status_code == 403
    data = response.get_json()
    assert data["message"] == "No provided output name"

def test_run_spider_nonexistent_spider(client):
    response = client.get('/run_spider', 
                            headers={'shrek_key': '12345'}, 
                            json={
                                "spider_name": "nonexistent-spider",
                                "output_name": "outputUrl.json"
                            })
    
    assert response.status_code == 404
    data = response.get_json()
    assert data["message"] == "There is no such spider: spider name : nonexistent-spider"

def test_run_spider_error_running_spider(client):
    # Mocking or adjusting the behavior of SpiderRunner can be done here if needed.
    response = client.get('/run_spider', 
                            headers={'shrek_key': '12345'}, 
                            json={
                                "spider_name": "aprox-spider",
                                "output_name": "outputUrl.json"
                            })
    
    assert response.status_code == 500
    data = response.get_json()
    assert data["message"] == "There was an error running this spider: aprox-spider"