import scrapy
from urllib.parse import urljoin
from airline.items import Product
from datetime import datetime


class AirlineSpider(scrapy.Spider):
    name = 'airline'
    allowed_domains = ['airline.su']
    start_urls = ['https://airline.su/catalogue/']

    def parse(self, response):
        main_cats = response.xpath("//a[contains(@class, 'category-submenu-link')]/@href").getall()

        for url in main_cats:
            yield response.follow(
                url,
                callback=self.parse_category,
                errback=self.errback_handler
            )

    def parse_category(self, response):
        product_links = self.get_product_links(response)
        if product_links:
            for product_url in product_links:
                yield response.follow(
                    product_url,
                    callback=self.parse_product,
                    errback=self.errback_handler
                )

        subcategories = response.xpath("//a[contains(@class, 'category-submenu-link')]/@href").getall()
        if subcategories:
            for url in subcategories:
                yield response.follow(
                    url,
                    callback=self.parse_category,
                    errback=self.errback_handler
                )

        next_page = response.xpath('//a[contains(@class, "page-next")]/@href').get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                errback=self.errback_handler
            )

    def get_product_links(self, response):
        product_links = response.xpath(
            "//div[contains(@class, 'products-list-item fix-prop-height')]//a/@href").getall()
        return list(set(link for link in product_links if link.startswith('/catalogue/')))

    def parse_product(self, response):
        item = Product()
        item['url'] = response.url
        item['name'] = response.xpath("//div[contains(@class, 'product-card-title')]/h1/text()").get('').strip()

        price = response.xpath("//div[contains(@class, 'product-card-prices-value')]/text()").get()
        item['price'] = ''.join(c for c in price if c.isdigit() or c == '.') if price else None

        item['code'] = response.xpath("//i[contains(@class, 'icon-copy-code')]/@data-code").get('').strip()

        desc = response.xpath("//div[@class='tabs-content active' and @id='description']//text()").getall()
        item['description'] = ' '.join(t.strip() for t in desc if t.strip()) or 'Нет описания'

        specs = response.xpath("//div[contains(@class, 'product-card-prop-item')]//text()").getall()
        item['specs'] = [s.strip() for s in specs if s.strip()] or ['Нет характеристик']

        images = response.xpath("//img/@src").getall()
        item['images'] = [urljoin(response.url, img) for img in images if '/upload/' in img and 'resize_cache' in img]

        breadcrumbs = response.xpath(
            "//div[contains(@class, 'breadcrumbs')]//a/text() | //div[contains(@class, 'breadcrumbs')]//span/text()").getall()
        item['categories'] = [b.strip() for b in breadcrumbs if b.strip()][1:]

        item['timestamp'] = datetime.now().isoformat()

        yield item

    def errback_handler(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}, Reason: {failure.value}")