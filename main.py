import json
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(filename='logs.txt', level=logging.INFO)

def extract_lines():
    with open('urls.json', 'r') as f:
        data = json.load(f)
        for row in data:
            url = row.get('website')
            yield url


def parse_main_page(url, results):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем статусный код ответа
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while fetching {url}: {e}")
        return None

    logging.info(f"{url} {response.status_code}")
    print('☁ ▅▒░☼‿☼░▒▅ ☁')
    soup = BeautifulSoup(response.content, 'html.parser')

    soup = remove_nav_and_footer(soup)
    text_by_tag = sort_text_by_tag(soup)
    results[url] = text_by_tag
    
    if response.history:
        redirect = response.url
        logging.info(f"The URL {url} has {len(response.history)} redirects to {redirect}")
        if "redirect link" not in results[url]:
            results[url]["redirect link"] = []
        results[url]["redirect link"].insert(0, redirect)  # Добавляем новую ссылку в список по ключу "redirect link"
        parse_main_page(redirect, results)

    return soup

 
def meta_tags(soup):
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else None
    image_tag = soup.find('meta', attrs={'property': 'og:image'})
    image = image_tag.get('content') if image_tag else None
    return description, image
    

def remove_nav_and_footer(soup):
    for tag in soup(['nav', 'footer', 'style', 'span', 'script', 'a', 'button', 'code', 'label', 'sup', 'b', 'li', 'br', 'cite', 'em', 'strong']):
        tag.decompose()
    return soup

def sort_text_by_tag(soup):
    text_by_tag = {}
    for tag in soup.find_all():
        if tag.string and tag.string.strip():
            if tag.name not in text_by_tag:
                text_by_tag[tag.name] = set()
            text_by_tag[tag.name].add(tag.string.strip())

    description, image = meta_tags(soup)
    text_by_tag['description'] = [description] if description else None
    text_by_tag['image'] = [image] if image else None
    
    return {tag: list(text_by_tag[tag]) for tag in text_by_tag if text_by_tag[tag]}
    

# удаляет одинаковые строки в одном теге
def remove_duplicates(results):
    for url in results:
        for tag in results[url]:
            new_list = []
            last_value = None
            for value in results[url][tag][::-1]:
                if value and value != last_value:
                    new_list.append(value)
                    last_value = value
            results[url][tag] = new_list
    return results

# удаляет одинаковый текст в разных тегах и сохраняет один раз
def remove_duplicate_values(results):
    for url in results:
        for tag in results[url]:
            unique_values = []
            duplicates = set()
            for value in results[url][tag]:
                if value in duplicates:
                    continue
                for other_tag in results[url]:
                    if tag == other_tag:
                        continue
                    if value in results[url][other_tag]:
                        duplicates.add(value)
                        break
                else:
                    unique_values.append(value)
            results[url][tag] = unique_values
    return results

def remove_empty_lists(results):
    for url in list(results.keys()):
        for tag in list(results[url].keys()):
            if not results[url][tag]:
                del results[url][tag]
        if not results[url]:
            del results[url]
    return results

def check_dict(results):
    if len(results.keys()) == 2:
        if 'title' in results.keys() and 'description' in results.keys():
            return False
        else:
            return True


if __name__ == '__main__':
    urls = extract_lines()
    results = {}
    for url in urls:
        parse_main_page(url, results)

    if check_dict(results):
        for url in results:
            for tag in results[url]:
                results[url][tag] = list(set(results[url][tag]))

        results = remove_duplicates(results)
        results = remove_duplicate_values(results)
        results = remove_empty_lists(results)

    with open('results.json', 'w') as f:
        json.dump(results, f, indent = 4)