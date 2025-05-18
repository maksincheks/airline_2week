from airline.pipelines import AirlinePipeline
from scrapy import signals

class FinalizePipelineMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_closed(self, spider):
        active_spiders = len(spider.crawler.engine.slot.scheduler)
        if active_spiders <= 1:
            AirlinePipeline.finalize()