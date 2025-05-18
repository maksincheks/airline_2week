import scrapy
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import logging
from scrapy.utils.response import response_status_message
from time import sleep
from airline.items import AirlineItem


class AirlineSpider(scrapy.Spider):
    name = 'airline'
    allowed_domains = ['airline.su']
    start_urls = ['https://airline.su/catalogue/']
    max_pagination_depth = 50

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 0.75,
        'AUTOTHROTTLE_ENABLED': True,
        'RETRY_TIMES': 5,
        'DEPTH_LIMIT': 50,
        'DUPEFILTER_DEBUG': True,
        'HTTPCACHE_ENABLED': False,
    }

    def parse(self, response):
        main_cats = response.css('ul.catalog.js-catalog-hover > li > a::attr(href)').getall()
        if not main_cats:
            main_cats = response.css('div.categories a::attr(href), nav.menu a::attr(href)').getall()

        self.logger.info(f"Found {len(main_cats)} main categories")

        for url in main_cats:
            yield response.follow(
                url,
                callback=self.parse_category_tree,
                meta={'category_path': [], 'depth': 1, 'page': 1},
                errback=self.errback_handler,
                dont_filter=False
            )

    def parse_category_tree(self, response):
        current_category = response.css('h1::text, .page-title::text').get('').strip()
        category_path = response.meta.get('category_path', [])

        # Добавляем категорию только если она не совпадает с последней
        if not category_path or current_category != category_path[-1]:
            category_path = category_path + [current_category]

        current_depth = response.meta.get('depth', 1)
        current_page = response.meta.get('page', 1)

        self.logger.info(
            f"Processing category (depth {current_depth}): {' > '.join(category_path)} | Page: {current_page}")

        yield from self.parse_category_products(response, category_path)

        subcategories = response.css('''
            div.catalog-section a[href*="/catalog/"],
            .subcategories a[href],
            div.section-item a[href],
            li.category-item a[href],
            a[href*="/category/"],
            div.subcategory a[href]
        ''').css('::attr(href)').getall()

        for url in subcategories:
            if current_depth < 50:
                yield response.follow(
                    url,
                    callback=self.parse_category_tree,
                    meta={
                        'category_path': category_path.copy(),
                        'depth': current_depth + 1,
                        'page': 1
                    },
                    errback=self.errback_handler
                )

        if current_page < self.max_pagination_depth:
            next_page = self.get_next_page_url(response.url, current_page)
            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse_category_tree,
                    meta={
                        'category_path': category_path.copy(),
                        'depth': current_depth,
                        'page': current_page + 1
                    },
                    errback=self.errback_handler
                )

    def get_next_page_url(self, current_url, current_page):
        parsed = urlparse(current_url)
        query = parse_qs(parsed.query)
        query['PAGEN_1'] = [str(current_page + 1)]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def parse_category_products(self, response, category_path):
        product_selectors = [
            'a[href*="/product/"]',
            'a[href*="/item/"]',
            'div.product-item a',
            'div.card a',
            'div.products-list-item a',
            'article.product a',
            'div.product-card a'
        ]

        product_links = []
        for selector in product_selectors:
            links = response.css(f'{selector}::attr(href)').getall()
            if links:
                product_links.extend(links)

        product_links = list(set(product_links))
        self.logger.info(f"Found {len(product_links)} products at {response.url}")

        for url in product_links:
            yield response.follow(
                url,
                callback=self.parse_product,
                meta={'category_path': category_path.copy()},
                errback=self.errback_handler
            )

    def parse_product(self, response):
        category_path = response.meta.get('category_path', [])
        full_category = ' > '.join([cat for cat in category_path if cat])

        item = AirlineItem()
        item['url'] = response.url
        item['category'] = full_category
        item['name'] = (response.css('h1::text').get('') or
                        response.css('title::text').get('').replace(' - airline.su', '')).strip()
        item['code'] = self.get_product_code(response)
        item['description'] = self.get_description(response)
        item['price'] = self.get_price(response)
        item['properties'] = self.get_specs(response)
        item['images'] = self.get_images(response)

        self.logger.debug(f"Added product: {item['name']}")
        return item

    def get_images(self, response):
        img_sources = []
        selectors = [
            'img[src*="/upload/"]::attr(src)',
            'img[data-src*="/upload/"]::attr(data-src)',
            'img[data-original*="/upload/"]::attr(data-original)'
        ]

        for selector in selectors:
            img_sources.extend([
                urljoin(response.url, src)
                for src in response.css(selector).getall()
                if not src.startswith('data:')
            ])

        return img_sources if img_sources else ['No images']

    def get_product_code(self, response):
        code_selectors = [
            'i.icon-copy-code::attr(data-code)',
            'span.product-code::text',
            'div.article::text',
            'div.product-id::text',
            '//*[contains(text(), "Артикул")]/following::text()[1]'
        ]

        for selector in code_selectors:
            code = response.css(selector).get() if '::' in selector else response.xpath(selector).get()
            if code and code.strip():
                return code.strip()
        return ''

    def get_description(self, response):
        desc_parts = []
        for sel in [
            'div#description',
            'div.product-detail-text',
            'div.description',
            'div.full-desc'
        ]:
            desc_parts.extend([
                t.strip() for t in response.css(f'{sel} ::text').getall()
                if t.strip() and len(t.strip()) > 10
            ])

        return '\n'.join(desc_parts) if desc_parts else 'No description'

    def get_price(self, response):
        price_selectors = [
            'div.product-card-prices-value::text',
            'span.price::text',
            'meta[itemprop="price"]::attr(content)',
            'div.price-value::text'
        ]

        for selector in price_selectors:
            price = response.css(selector).get('')
            if price:
                clean_price = price.replace(' руб.', '').replace('₽', '').replace(' ', '').strip()
                if clean_price.isdigit():
                    return clean_price
        return ''

    def get_specs(self, response):
        specs = []

        for row in response.css('table.properties tr, table.characteristics tr'):
            cols = row.css('td::text, th::text, td span::text').getall()
            if len(cols) >= 2:
                spec = f"{cols[0].strip()}: {cols[1].strip()}"
                if len(spec) > 5:
                    specs.append(spec)

        for block in response.css('div.product-card-prop-full, div.product-card-prop-list'):
            text = ' | '.join([
                t.strip() for t in block.css('::text').getall()
                if t.strip() and len(t.strip()) > 2
            ])
            if text:
                specs.append(text)

        return '\n'.join(specs) if specs else 'Not specified'

    def errback_handler(self, failure):
        self.logger.error(f"Error processing {failure.request.url}: {failure.value}")
        if failure.check(scrapy.exceptions.IgnoreRequest):
            self.logger.warning(f"Request was ignored: {failure.request.url}")