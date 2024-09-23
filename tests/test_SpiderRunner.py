import pytest
import subprocess
import os

from app.api_manager import SpiderRunner

@pytest.fixture
def spider_runner():
    pass
    


def test_constructor():
    s_name = 'test_spider'
    output_file = 'output.json'
    args = ('arg1', 'arg2')
    kwargs = {'key1': 'value1', 'key2': 'value2'}

    spider_runner = SpiderRunner(spider_name=s_name, output_file=output_file, category = "something")

    assert spider_runner.spider_name == s_name
    assert spider_runner.output_file == output_file