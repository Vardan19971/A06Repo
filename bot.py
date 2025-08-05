import requests
import time
import os
import json
from urllib.parse import unquote

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
PRICE_LIMIT_RUB = 7700  # лимит цены в рублях

def send_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": USER_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def check_wb():
    print("=== Проверка WildBerries ===")
    url = "https://card.wb.ru/cards/v1/list"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "123585351",  # Москва
        "sort": "popular",
        "spp": "30",
        "query": "samsung a06"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        products = r.json().get("data", {}).get("products", [])
        if not products:
            print("WB: товары не найдены")
        for product in products:
            name = product.get("name", "")
            price_rub = product.get("salePriceU", 0) / 100
            print(f"WB: {name} — {price_rub} ₽")
            if price_rub <= PRICE_LIMIT_RUB:
                link = f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
                send_message(f"🔥 WildBerries: {name}\nЦена: {price_rub} ₽\nСсылка: {link}")
    except Exception as e:
        print(f"Ошибка WB: {e}")
        send_message(f"⚠ Ошибка WB: {e}")

def check_ozon():
    print("=== Проверка Ozon ===")
    url = "https://api.ozon.ru/composer-api.bx/page/json/v2"
    params = {"url": "/search/?from_global=true&text=Galaxy%20A06"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        widget_states = r.json().get("widgetStates", {})
        found = False
        for key, value in widget_states.items():
            if "searchResultsV2" in key:
                try:
                    decoded = unquote(value)
                    products_data = json.loads(decoded)
                    items = products_data.get("items", [])
                    for item in items:
                        product = item.get("cellTrackingInfo", {}).get("product", {})
                        name = product.get("title", "")
                        price_rub = product.get("price", {}).get("price", 0)
                        print(f"Ozon: {name} — {price_rub} ₽")
                        if price_rub <= PRICE_LIMIT_RUB:
                            link = "https://www.ozon.ru" + item.get("link", "")
                            send_message(f"🔥 Ozon: {name}\nЦена: {price_rub} ₽\nСсылка: {link}")
                        found = True
                except Exception as e:
                    print(f"Ошибка парсинга Ozon: {e}")
        if not found:
            print("Ozon: товары не найдены")
    except Exception as e:
        print(f"Ошибка Ozon: {e}")
        send_message(f"⚠ Ошибка Ozon: {e}")

if __name__ == "__main__":
    send_message(f"✅ Бот запущен. Лимит: {PRICE_LIMIT_RUB} ₽. Проверка каждые 2 минуты.")
    offset = 0
    while True:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}", timeout=10).json()
            for update in updates.get("result", []):
                message = update.get("message")
                if message and message.get("text") == "/start":
                    send_message("✅ Бот работает!")
                offset = update['update_id'] + 1

            check_wb()
            check_ozon()

        except Exception as e:
            print(f"Общая ошибка: {e}")
            send_message(f"⚠ Общая ошибка: {e}")

        time.sleep(120)
