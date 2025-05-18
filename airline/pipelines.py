import os
from datetime import datetime
import threading
from openpyxl import Workbook


class AirlinePipeline:
    lock = threading.Lock()
    initialized = False
    wb = None
    filename = None

    def __init__(self):
        if not AirlinePipeline.initialized:
            with AirlinePipeline.lock:
                if not AirlinePipeline.initialized:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    AirlinePipeline.filename = f"outputs/airline_combined_{timestamp}.xlsx"

                    if not os.path.exists('outputs'):
                        os.makedirs('outputs')

                    AirlinePipeline.wb = Workbook()
                    ws = AirlinePipeline.wb.active
                    ws.title = "Товары"
                    headers = ['URL', 'Категория', 'Название', 'Код товара',
                               'Описание', 'Цена', 'Характеристики', 'Изображения']
                    ws.append(headers)
                    AirlinePipeline.initialized = True

    def process_item(self, item, spider):
        with AirlinePipeline.lock:
            ws = AirlinePipeline.wb.active

            category_path = item.get('category', '')
            if ' > ' in category_path:
                categories = category_path.split(' > ')
                unique_categories = []
                last_category = ''
                for cat in categories:
                    if cat.strip() != last_category:
                        unique_categories.append(cat.strip())
                        last_category = cat.strip()
                cleaned_category = ' > '.join(unique_categories)
            else:
                cleaned_category = category_path

            row = [
                item.get('url', ''),
                cleaned_category,
                item.get('name', ''),
                item.get('code', ''),
                item.get('description', ''),
                item.get('price', ''),
                item.get('properties', ''),
                ', '.join(item.get('images', [])) if isinstance(item.get('images', []), list) else item.get('images',
                                                                                                            '')
            ]
            ws.append(row)

        return item

    def close_spider(self, spider):
        # Сохранение будет выполнено при закрытии последнего паука
        pass

    @classmethod
    def finalize(cls):
        if cls.wb and cls.filename:
            with cls.lock:
                cls.wb.save(cls.filename)