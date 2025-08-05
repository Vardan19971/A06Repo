import requests
import time
import os
import json
import random
from urllib.parse import unquote

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
PRICE_LIMIT_RUB = 7700
SEARCH_QUERY = "Samsung A06"

# Список User-Agent для ротации, чтобы снизить вероятность блокировки
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/109.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.128 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
]

def send_message(text):
    """Отправляет сообщение в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": USER_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"Сообщение отправлено.")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

def get_random_headers():
    """Возвращает случайный набор заголовков."""
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }

def check_wildberries():
    """Проверяет цены на Wildberries."""
    print(f"=== Проверка Wildberries на {SEARCH_QUERY} ===")
    url = "https://catalog.wb.ru/catalog/exactmatch/v4/products"
    params = {
        "appType": 1,
        "curr": "rub",
        "dest": -1257723,
        "regions": "80,38,4,64,83,33,68,70,69,30,22,66,48,1,31,6,40,71",
        "query": SEARCH_QUERY,
        "resultset": "catalog",
        "spp": 29
    }

    try:
        response = requests.get(url, params=params, headers=get_random_headers(), timeout=15)
        response.raise_for_status()
        data = response.json()

        products = data.get("data", {}).get("products", [])
        if not products:
            print("WB: Товары не найдены.")
            return

        for product in products:
            name = product.get("name", "Название не найдено")
            price_in_rub = product.get("salePriceU", 0) / 100
            if price_in_rub <= PRICE_LIMIT_RUB and SEARCH_QUERY.lower() in name.lower():
                product_id = product.get("id")
                link = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
                msg = f"🔥 *Wildberries*\n\n*Товар:* {name}\n*Цена:* {price_in_rub} ₽\n[Ссылка на товар]({link})"
                send_message(msg)
                
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса Wildberries: {e}")
        send_message(f"⚠ *Ошибка Wildberries:* Не удалось получить данные. Попробуйте снова.")
    except Exception as e:
        print(f"Неожиданная ошибка Wildberries: {e}")
        send_message(f"⚠ *Ошибка Wildberries:* Произошла непредвиденная ошибка.")

def check_ozon():
    """Проверяет цены на Ozon."""
    print(f"=== Проверка Ozon на {SEARCH_QUERY} ===")
    url = "https://www.ozon.ru/search/"
    params = {
        "text": SEARCH_QUERY
    }
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Ozon теперь часто отдаёт JS-код. Проще найти данные в HTML-странице.
        if "catalogItems" in response.text:
            start_index = response.text.find('"catalogItems":[') + len('"catalogItems":[') -1
            end_index = response.text.find('],"filters"', start_index)
            
            json_str = response.text[start_index:end_index] + "]"
            
            products_data = json.loads(json_str)
            found_product = False
            
            for item in products_data:
                name = item.get("mainState", [{}])[0].get("title", "Название не найдено")
                price = item.get("mainState", [{}])[1].get("atom", {}).get("price", {}).get("price", 0)
                
                if price and price <= PRICE_LIMIT_RUB and SEARCH_QUERY.lower() in name.lower():
                    link = "https://www.ozon.ru" + item.get("action", {}).get("link", "")
                    msg = f"🔥 *Ozon*\n\n*Товар:* {name}\n*Цена:* {price} ₽\n[Ссылка на товар]({link})"
                    send_message(msg)
                    found_product = True
            
            if not found_product:
                print("Ozon: Товары не найдены.")
        else:
            print("Ozon: Не удалось найти данные о товарах на странице.")
            send_message(f"⚠ *Ошибка Ozon:* Структура страницы изменилась. Бот требует обновления.")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса Ozon: {e}")
        send_message(f"⚠ *Ошибка Ozon:* Не удалось получить данные. Попробуйте снова.")
    except Exception as e:
        print(f"Неожиданная ошибка Ozon: {e}")
        send_message(f"⚠ *Ошибка Ozon:* Произошла непредвиденная ошибка.")

if __name__ == "__main__":
    send_message(f"✅ *Бот запущен!*\n\nМониторинг товара: *{SEARCH_QUERY}*\nЛимит цены: *{PRICE_LIMIT_RUB} ₽*\nПроверка будет производиться каждые 2 минуты.")
    
    while True:
        try:
            check_wildberries()
            check_ozon()
        except Exception as e:
            print(f"Общая ошибка в основном цикле: {e}")
            send_message(f"⚠ *Критическая ошибка:* Произошла непредвиденная ошибка в основном цикле бота. Проверьте логи.")
            
        print("---")
        time.sleep(120)  # Пауза 2 минуты
