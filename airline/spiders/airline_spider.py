import scrapy
from urllib.parse import urljoin
from typing import Generator, Iterable
from scrapy.http import Request, Response
from airline.items import ProductItem
from datetime import datetime


class AirlineSpider(scrapy.Spider):
    name = 'airline'
    allowed_domains = ['airline.su']
    start_urls = ['https://airline.su/catalogue/']

    def parse(self, response: Response) -> Iterable[Request]:
        main_cats = response.xpath("//a[contains(@class, 'category-submenu-link')]/@href").getall()

        for url in main_cats:
            yield Request(
                url=urljoin(response.url, url),
                callback=self.parse_category,
                errback=self.errback_handler
            )

    def parse_category(self, response: Response) -> Iterable[Request]:
        category_name = response.xpath("//h1/text()").get('').strip()

        last_page = response.xpath('//a[contains(@class, "page-last")]/@href').get()
        total_pages = 1
        if last_page:
            try:
                total_pages = int(last_page.split('=')[-1])
            except (IndexError, ValueError):
                self.logger.warning(f"Could not parse total pages for {response.url}")

        self.logger.info(f"Parsing category: {category_name}, total pages: {total_pages}")

        yield from self.parse_page(response, category_name, 1)

        for page in range(2, total_pages + 1):
            page_url = f"{response.url}?PAGEN_1={page}"
            yield Request(
                url=page_url,
                callback=self.parse_page,
                errback=self.errback_handler,
                meta={
                    "page": page,
                    "category": category_name,
                }
            )

        subcategories = response.xpath("//a[contains(@class, 'category-submenu-link')]/@href").getall()
        for url in subcategories:
            yield Request(
                url=urljoin(response.url, url),
                callback=self.parse_category,
                errback=self.errback_handler
            )

    def parse_page(self, response: Response, category: str = None, page: int = None) -> Iterable[Request]:
        if category is None or page is None:
            category = response.meta.get('category', 'unknown')
            page = response.meta.get('page', 1)

        self.logger.info(f"Parsing page {page} of category '{category}'. URL: {response.url}")

        product_links = self.get_product_links(response)
        for product_url in product_links:
            yield Request(
                url=urljoin(response.url, product_url),
                callback=self.parse_product,
                errback=self.errback_handler,
                meta={'category': category}
            )

    def get_product_links(self, response: Response) -> list[str]:
        product_links = response.xpath(
            "//div[contains(@class, 'products-list-item fix-prop-height')]//a/@href").getall()
        return list(set(link for link in product_links if link.startswith('/catalogue/')))

    def parse_product(self, response: Response) -> Generator[ProductItem, None, None]:
        item = ProductItem()
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