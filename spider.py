import scrapy
from scrapy import Selector


class CryptoSpider(scrapy.Spider):
    name = "crypt"
    url = 'https://bitcointalk.org/index.php?board=7.'

    def start_request(self):
        for i in range(10):
            yield scrapy.Request(self.url + str(i * 40))

    def parse(self, response):
        topics = Selector(response).xpath("//a[contains(@href, 'https://bitcointalk.org/index.php?topic')]")
        for topic in topics:
            url = response.urljoin(topic.xpath(".//@href").extract_first())
            request = scrapy.Request(url, callback=self.parse_thread_pages)
            request.meta['topic'] = topic.xpath('.//text()').extract_first()
            yield request

    def parse_thread_pages(self, response):
        sel = Selector(response) \
            .xpath("//a[contains(@class,'navPages)]/@href")
        pages = sel.re_first(r'.*topic=(\d+\.\d+)')
        link = sel.re_first(r'(.*topic=).*')
        if pages is None:
            yield from self.parse_thread_messages(response)
        else:
            for p in range(int(pages)):
                url = response.urljoin(link + str((p + 1)*40))
                request = scrapy.Request(url, callback=self.parse_thread_messages)
                request.meta['topic'] = response.meta['topic']
                yield request

    def parse_thread_messages(self, response):
        topic = response.meta['topic']
        messages = Selector(response).xpath("//div[contains(@id, 'post_message_')]/text()").re(r"\r*\n*\s*(.+)")
        authors = Selector(response).xpath("//a[contains(@title, 'View the profile of')]/text()")
        dates = Selector(response) \
            .xpath("//table[contains(@id, 'post')]/tr/td[contains(@class, 'thead')]") \
            .re(r'.*(\d{2}-\d{2}-\d{4},\s\d{2}:\d{2}\s[A-Za-z]{2}).*')
        for item in zip(authors, messages, dates):
            if len(item[1].strip()) > 0:
                yield {
                    'topic': topic,
                    'author': item[0],
                    'message': item[1],
                    'date': item[2]
                }