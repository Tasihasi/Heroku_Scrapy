import pytest, random
from app.heroku_scrapy.heroku_scrapy.proxy_manager import ProxyHandler


@pytest.fixture
def proxy_handler():
    return ProxyHandler()




