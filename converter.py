import json
import os
from openpyxl import Workbook


def convert_to_excel():
    json_files = [f for f in os.listdir('data')
                  if f.startswith('products_') and f.endswith('.json')]

    if not json_files:
        print("Не найдено JSON-файлов в папке data")
        return

    print("\nНайдены следующие JSON-файлы:")
    for i, f in enumerate(json_files, 1):
        print(f"{i}. {f}")

    unique_products = {}

    for json_file in json_files:
        file_path = os.path.join('data', json_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"\nФайл {json_file}: {len(data)} товаров")
                    for product in data:
                        url = product.get('url')
                        if url and url not in unique_products:
                            unique_products[url] = product
                else:
                    print(f"Файл {json_file} содержит данные не в формате списка")
        except Exception as e:
            print(f"Ошибка при чтении файла {json_file}: {str(e)}")
            continue

    if not unique_products:
        print("\nНет данных для конвертации")
        return

    print(f"\nИтого уникальных товаров: {len(unique_products)}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Товары"

    headers = [
        'URL', 'Категории', 'Название', 'Артикул',
        'Описание', 'Цена', 'Характеристики', 'Изображения'
    ]
    ws.append(headers)

    for product in unique_products.values():
        row = [
            product.get('url', ''),
            ' » '.join(product.get('categories', [])),
            product.get('name', ''),
            product.get('code', ''),
            product.get('description', ''),
            product.get('price', ''),
            '\n'.join(product.get('specs', [])),
            '\n'.join(product.get('images', []))
        ]
        ws.append(row)

    column_widths = {
        'A': 50, 'B': 30, 'C': 40, 'D': 15,
        'E': 60, 'F': 15, 'G': 40, 'H': 30
    }
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width

    output_file = os.path.join('data', 'combined_products.xlsx')
    try:
        wb.save(output_file)
        print(f"\nРезультат сохранен в {output_file}")
    except Exception as e:
        print(f"\nОшибка при сохранении файла: {str(e)}")


if __name__ == '__main__':
    convert_to_excel()