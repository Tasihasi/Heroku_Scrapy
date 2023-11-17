import scrapy
import re
import json
import os
import time

class FreeProxyListSpider(scrapy.Spider):
    name = 'free_proxy_list2'
    start_urls = ['https://free-proxy-list.net/']

    def parse(self, response):
        # Check if the "Get raw list" link is present in the page source
        raw_list_link = response.css('a[title="Get raw list"][data-toggle="modal"]::attr(href)').get()

        if raw_list_link:
            # Extract the link
            raw_list_url = response.urljoin(raw_list_link)
            yield {
                'raw_list_url': raw_list_url,
            }
            
            # Now, let's extract the content of the <textarea>
            textarea_content = response.css('textarea.form-control[readonly="readonly"]::text').get()
            if textarea_content:
                # You can extract the desired content here
                yield {
                    'textarea_content': textarea_content.strip(),
                }
                
                # Save the extracted content to a text file
                self.save_to_file(textarea_content.strip())
            else:
                self.logger.warning('Textarea content not found on the page.')
        else:
            self.logger.warning('"Get raw list" link not found on the page.')

    def save_to_file(self, content):
        with open('proxies.txt', 'w') as file:
            file.write(content)
