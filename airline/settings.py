import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

BOT_NAME = 'airline'
SPIDER_MODULES = ['airline.spiders']
NEWSPIDER_MODULE = 'airline.spiders'

ROBOTSTXT_OBEY = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Основные настройки
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.5
AUTOTHROTTLE_ENABLED = True
FEED_EXPORT_ENCODING = 'utf-8'
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'scrapy.log'

ITEM_CLASSES = ['airline.items.ProductItem']

# Настройки экспорта
FEEDS = {
    'data/products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'item_classes': ITEM_CLASSES,
        'overwrite': True
    }
}