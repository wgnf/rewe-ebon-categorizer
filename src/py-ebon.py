from pypdf import PdfReader
import os
import sys
import itertools
import re
import json

bought_items = []
category_config = []
category_config_file = 'category_config.json'

def main():
    try:
        execute()
    finally:
        save_category_config()

def execute() -> None:
    global category_config
    load_category_config()

    print('which file should be processed? (PDF)')
    filepath = input()
    parse_bought_items(filepath)

    while True:
        clear()
        print_bought_items()
        
        print('\n\ndo you want to edit the current category assignment? Y/N')
        decision = input()
        if decision != 'Y' and decision != 'y':
            break
        
        edit_mode()

def load_category_config() -> None:
    global category_config, category_config_file

    print('loading configuration...')
    if not os.path.isfile(category_config_file):
        return
    
    with open(category_config_file, 'r') as file_stream:
        parsed_config = json.load(file_stream)

    category_config = parsed_config

def save_category_config() -> None:
    global category_config

    print('saving configuration...')
    with open(category_config_file, 'w') as file_stream:
        json.dump(category_config, file_stream)

def parse_bought_items(filepath: str) -> None:
    global bought_items

    filepath = filepath.replace('"', '')
    filetext = get_text_from_pdf(filepath)
    file_lines = filetext.split('\n')

    # list of bought items starts after a single line with "EUR" far to the right   
    filter_iter = itertools.dropwhile(lambda line: 'EUR' not in line, file_lines)
    # and ends when the sum is printed out after a long array of dashes
    filter_iter = itertools.takewhile(lambda line: '-----' not in line, filter_iter)
    # important, because when you buy multiple things, the amount of items is printed out in a separate line
    filter_iter = filter(lambda line: not line.startswith(' '), filter_iter)
    filter_iter = map(lambda line: line.strip(), filter_iter)

    bought_item_texts = list(filter_iter)

    for bought_item_text in bought_item_texts:
        match = re.search('(?P<name>.*)(\s{2,})(?P<price>\S*)', bought_item_text)

        item_name = match.group('name').strip()
        price = match.group('price')
        price = price.replace(',', '.')
        bought_item = {
            'name': item_name,
            'price': float(price),
            'category_id': get_category_id_from_item_name(item_name)
        }
    
        bought_items.append(bought_item)

def get_text_from_pdf(filepath: str) -> str:
    if not os.path.isfile(filepath):
        sys.exit(f'file "{filepath}" does not exist!')

    reader = PdfReader(filepath)

    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_category_id_from_item_name(item_name: str) -> int|None:
    global category_config

    index = 0
    for category in category_config:
        if 'assigned_products' not in category:
            return None

        if item_name in category['assigned_products']:
            return index
        
        index += 1
    return None

def print_bought_items() -> None:
    global bought_items
    index = 0
    for bought_item in bought_items:
        print(f'[{str(index).rjust(3)}] {bought_item["name"].ljust(25)} {get_category_name_by_id(bought_item["category_id"]).ljust(15)} {bought_item["price"]:.2f}€')
        index += 1
    
    print('\n------------------------\n')
    
    sorted_bought_items = bought_items.copy()
    sorted_bought_items.sort(key=get_category_id)

    for category_id, grouped_items in itertools.groupby(sorted_bought_items, lambda item: item['category_id']):
        print(f'{get_category_name_by_id(category_id).ljust(15)} {sum([item["price"] for item in grouped_items]):.2f}€')

    total_sum = sum(item['price'] for item in bought_items)
    print(f'\nTOTAL: {total_sum:.2f}€')

def get_category_name_by_id(category_id: int|None) -> str:
    global category_config

    if category_id is None:
        return 'Unknown'
    category = category_config[category_id]
    return category['name']

def edit_mode() -> None:
    global bought_items

    print('which item do you want to change? use "c" to cancel')
    decision = input()
    if decision == 'C' or decision == 'c':
        return
    
    item_id_to_edit = int(decision)
    item = bought_items[item_id_to_edit]

    print(f'item to edit: "{item["name"]}", with the current category "{get_category_name_by_id(item["category_id"])}"')

    print()

    print('you can (use "c" to cancel):')
    print('"e":  edit category')
    print('"es": edit category and save decision to the configuration')

    decision = input()
    if decision == 'C' or decision == 'c':
        return
    
    if decision == 'E' or decision == 'e':
        edit_category(item, False)

    if decision == 'ES' or decision == 'es':
        edit_category(item, True)

def edit_category(item: dict[str, any], save_to_config: bool) -> None:
    global category_config

    print()
    print('you can cancel ("c"), you can add a new category ("a") and you can choose one of the already existing categories:')

    index = 0
    for category in category_config:
        print(f'[{str(index).rjust(3)}] {category["name"].ljust(15)}')
        index += 1

    print()
    decision = input()

    if decision == 'C' or decision == 'c':
        return
    
    if decision == 'A' or decision == 'a':
        category_id = add_and_use_category()
    else:
        category_id = int(decision)
    
    item['category_id'] = category_id

    if save_to_config:
        category = category_config[category_id]
        if 'assigned_products' not in category:
            category['assigned_products'] = []

        category['assigned_products'].append(item['name'])

def add_and_use_category() -> int:
    global category_config

    print('what should the new category be called?')
    category_name = input()

    category = {
        'name': category_name
    }
    category_config.append(category)
    return len(category_config) - 1

def clear() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

def get_category_id(item: dict[str, any]) -> int:
    category_id = item['category_id']
    actual_category_id = category_id if category_id is not None else -1
    return actual_category_id

if __name__ == '__main__':
    main()
