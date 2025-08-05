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
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }

def check_wildberries():
    """Проверяет цены на Wildberries, используя другой API."""
    print(f"=== Проверка Wildberries на {SEARCH_QUERY} ===")
    url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest=123585351&query={SEARCH_QUERY}&resultset=catalog&sort=popular&spp=30"
    
    try:
        response = requests.get(url, headers=get_random_headers(), timeout=15)
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
    """Проверяет цены на Ozon, используя другой подход."""
    print(f"=== Проверка Ozon на {SEARCH_QUERY} ===")
    url = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
    params = {
        "url": f"/search/?text={SEARCH_QUERY.replace(' ', '+')}"
    }
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.ozon.ru/",
        "Origin": "https://www.ozon.ru",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        widget_states = data.get("widgetStates", {})
        found_product = False
        
        for key, value in widget_states.items():
            if "searchResultsV2" in key:
                try:
                    widget_data = json.loads(unquote(value))
                    items = widget_data.get("items", [])
                    
                    for item in items:
                        product_info = item.get("cellTrackingInfo", {}).get("product", {})
                        name = product_info.get("title", "Название не найдено")
                        price = product_info.get("price", {}).get("price", 0)
                        
                        if price and price <= PRICE_LIMIT_RUB and SEARCH_QUERY.lower() in name.lower():
                            link = f"https://www.ozon.ru{item.get('link')}"
                            msg = f"🔥 *Ozon*\n\n*Товар:* {name}\n*Цена:* {price} ₽\n[Ссылка на товар]({link})"
                            send_message(msg)
                            found_product = True
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Ошибка при парсинге данных Ozon: {e}")

        if not found_product:
            print("Ozon: Товары не найдены.")
            
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
            time.sleep(10)  # Задержка между запросами к разным сайтам
            check_ozon()
        except Exception as e:
            print(f"Общая ошибка в основном цикле: {e}")
            send_message(f"⚠ *Критическая ошибка:* Произошла непредвиденная ошибка в основном цикле бота. Проверьте логи.")
            
        print("---")
        time.sleep(110) # 10 секунд + 110 = 120 секунд (2 минуты)
