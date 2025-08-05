import requests
import time
import os
import json
from urllib.parse import unquote

BOT_TOKEN = os.getenv("BOT_TOKEN")      # Токен бота
USER_ID = int(os.getenv("USER_ID"))     # Твой Telegram ID
PRICE_LIMIT_RUB = 7700                   # Лимит цены в рублях

def send_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": USER_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def check_wb():
    print("=== Проверка WildBerries ===")
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "123585351",
        "query": "Samsung A06",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        products = data.get("data", {}).get("products", [])
        if not products:
            print("WB: товары не найдены")
        for product in products:
            name = product.get("name", "")
            price = product.get("salePriceU", 0) / 100
            if price <= PRICE_LIMIT_RUB and "a06" in name.lower():
                link = f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
                msg = f"🔥 WildBerries\n{name}\nЦена: {price} ₽\n{link}"
                print(msg)
                send_message(msg)
    except Exception as e:
        print(f"Ошибка WB: {e}")
        send_message(f"⚠ Ошибка WildBerries: {e}")

def check_ozon():
    print("=== Проверка Ozon ===")
    url = "https://api.ozon.ru/composer-api.bx/page/json/v2"
    params = {
        "url": "/category/telefony-i-smart-chasy-15501/?category_was_predicted=true&deny_category_prediction=true&from_global=true&text=samsung+a06"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.ozon.ru/category/telefony-i-smart-chasy-15501/",
        "Origin": "https://www.ozon.ru",
        "Connection": "keep-alive",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        widget_states = data.get("widgetStates", {})
        found = False
        for key, val in widget_states.items():
            if "searchResultsV2" in key:
                decoded = unquote(val)
                products_data = json.loads(decoded)
                items = products_data.get("items", [])
                for item in items:
                    product = item.get("cellTrackingInfo", {}).get("product", {})
                    name = product.get("title", "")
                    price = product.get("price", {}).get("price", 0)
                    if price <= PRICE_LIMIT_RUB and "a06" in name.lower():
                        link = "https://www.ozon.ru" + item.get("link", "")
                        msg = f"🔥 Ozon\n{name}\nЦена: {price} ₽\n{link}"
                        print(msg)
                        send_message(msg)
                        found = True
        if not found:
            print("Ozon: товары не найдены")
    except Exception as e:
        print(f"Ошибка Ozon: {e}")
        send_message(f"⚠ Ошибка Ozon: {e}")

if __name__ == "__main__":
    send_message(f"✅ Бот запущен. Проверяю Samsung A06. Лимит цены: {PRICE_LIMIT_RUB} ₽. Проверка каждые 2 минуты.")
    offset = 0
    while True:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}", timeout=10).json()
            for update in updates.get("result", []):
                message = update.get("message")
                if message and message.get("text") == "/start":
                    send_message("✅ Бот работает и мониторит цены Samsung A06.")
                offset = update['update_id'] + 1

            check_wb()
            check_ozon()

        except Exception as e:
            print(f"Общая ошибка: {e}")
            send_message(f"⚠ Общая ошибка: {e}")

        time.sleep(120)  # Проверяем каждые 2 минуты
