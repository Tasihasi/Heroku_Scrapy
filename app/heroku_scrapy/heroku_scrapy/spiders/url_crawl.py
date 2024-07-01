import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class UrlCrawlSpider(CrawlSpider):
    name = "url-crawl"


    
   
