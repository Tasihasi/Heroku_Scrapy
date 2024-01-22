# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# pipelines.py

import json

class JsonLinesWriterPipeline:
    def __init__(self, output_file):
        self.output_file = output_file
        self.file = None

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get('JSONL_OUTPUT_FILE', 'output.json')
        return cls(output_file)

    def open_spider(self, spider):
        self.file = open(self.output_file, 'w', encoding='utf-8')

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

    def close_spider(self, spider):
        if self.file:
            self.file.close()
