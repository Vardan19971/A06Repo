import requests
import time
import os
import json
from urllib.parse import unquote

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
PRICE_LIMIT_RUB = 7700
SEARCH_QUERY = "Samsung A06"

def send_message(text):
    """Отправляет сообщение в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": USER_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"Сообщение отправлено: {text}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        products = data.get("data", {}).get("products", [])
        if not products:
            print("WB: Товары не найдены.")
            return

        for product in products:
            name = product.get("name", "Название не найдено")
            price_in_rub = product.get("salePriceU", 0) / 100
            
            # Проверяем, соответствует ли цена лимиту и ищем в названии ключевые слова.
            if price_in_rub <= PRICE_LIMIT_RUB and SEARCH_QUERY.lower() in name.lower():
                product_id = product.get("id")
                link = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
                msg = f"🔥 *Wildberries*\n\n*Товар:* {name}\n*Цена:* {price_in_rub} ₽\n[Ссылка на товар]({link})"
                send_message(msg)
                
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса Wildberries: {e}")
        send_message(f"⚠ *Ошибка Wildberries:* Не удалось получить данные. Проверьте подключение или логи.")
    except Exception as e:
        print(f"Неожиданная ошибка Wildberries: {e}")
        send_message(f"⚠ *Ошибка Wildberries:* Произошла непредвиденная ошибка.")

def check_ozon():
    """Проверяет цены на Ozon."""
    print(f"=== Проверка Ozon на {SEARCH_QUERY} ===")
    url = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
    params = {
        "url": f"/search/?text={SEARCH_QUERY.replace(' ', '+')}"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://www.ozon.ru/"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
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
        send_message(f"⚠ *Ошибка Ozon:* Не удалось получить данные. Проверьте подключение или логи.")
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
