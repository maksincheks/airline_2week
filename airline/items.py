import scrapy

class AirlineItem(scrapy.Item):
    url = scrapy.Field()
    category = scrapy.Field()
    name = scrapy.Field()
    code = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    properties = scrapy.Field()
    images = scrapy.Field()