import scrapy
from scrapy.spiders import Spider
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import hashlib

class DemospiderSpider(Spider):
    name = "demospider"
    allowed_domains = ["voz.vn"]
    start_urls = ["https://voz.vn/whats-new"]
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Process one request at a time
        'DOWNLOAD_DELAY': 1,  # Add delay between requests
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': True,
    }
    
    def extract_thread_id(self, url):
        # Extract thread ID from URL
        parsed = urlparse(url)
        path_parts = parsed.path.split('.')
        if len(path_parts) > 1:
            return path_parts[-1]
        return None
    
    def generate_item_id(self, thread_url, timestamp):
        # Create a unique ID using thread ID and timestamp
        thread_id = self.extract_thread_id(thread_url)
        if thread_id and timestamp:
            # Create a string combining thread ID and timestamp
            id_string = f"{thread_id}_{timestamp}"
            # Generate a hash of the combined string
            return hashlib.md5(id_string.encode()).hexdigest()
        return None
    
    def parse(self, response):
        # Get all thread containers in order
        thread_containers = response.xpath("//div[contains(@class, 'structItem structItem--thread')]")
        
        # Create a list to store all threads with their metadata
        threads = []
        
        for thread in thread_containers:
            latest_link = thread.xpath(".//div[@class='structItem-cell structItem-cell--latest']//a[contains(@href, '/latest')]/@href").get()
            if latest_link:
                thread_url = urljoin(response.url, latest_link)
                thread_date_str = thread.xpath(".//div[@class='structItem-cell structItem-cell--main']//time/@datetime").get()
                
                thread_info = {
                    'url': thread_url,
                    'thread_title': thread.xpath(".//div[@class='structItem-title']//a/text()").get(),
                    'thread_date': thread_date_str,
                    'timestamp': datetime.fromisoformat(thread_date_str.replace('Z', '+00:00')) if thread_date_str else None
                }
                threads.append(thread_info)
        
        # Sort threads by timestamp, newest first
        sorted_threads = sorted(threads, 
                              key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min,
                              reverse=True)
        
        # Process threads in order
        for thread in sorted_threads:
            yield scrapy.Request(
                thread['url'],
                callback=self.parse_latest_message,
                meta={'thread_info': thread},
                dont_filter=True  # Ensure the request is processed even if URL was seen before
            )
    
    def parse_latest_message(self, response):
        thread_info = response.meta['thread_info']
        
        # Find the last message container
        message_container = response.xpath("//article[contains(@class, 'message message--post')]")[-1]
        
        if message_container:
            # Extract the message content, excluding quoted text
            message_content = message_container.xpath(".//div[contains(@class, 'message-userContent')]//div[@class='bbWrapper']//text()[not(ancestor::blockquote)]").getall()
            message_content = ' '.join([text.strip() for text in message_content if text.strip()])
            
            # Get the username of the poster
            username = message_container.xpath(".//h4[@class='message-name']//span[@itemprop='name']/text()").get()
            
            # Get the post timestamp
            timestamp = message_container.xpath(".//time[@class='u-dt']/@datetime").get()
            
            # Generate unique ID for this item
            item_id = self.generate_item_id(response.url, timestamp)
            
            yield {
                'id': item_id,
                'thread_title': thread_info['thread_title'],
                'thread_date': thread_info['thread_date'],
                'latest_poster': username,
                'latest_post_time': timestamp,
                'message_content': message_content,
                'thread_url': response.url
            }