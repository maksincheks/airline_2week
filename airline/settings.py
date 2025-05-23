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
CONCURRENT_REQUESTS = 2  # Было 16, но в spider стояло 2
DOWNLOAD_DELAY = 3.0     # Было 0.5, но в spider стояло 3.0
AUTOTHROTTLE_ENABLED = True
FEED_EXPORT_ENCODING = 'utf-8'
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'scrapy.log'

# Явно указываем классы Items
ITEM_CLASSES = ['airline.items.Product']

# Настройки экспорта
FEEDS = {
    'data/products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'item_classes': ITEM_CLASSES,
        'overwrite': True
    }
}