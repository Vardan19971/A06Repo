import requests
import time
import os
import json
from urllib.parse import unquote

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
PRICE_LIMIT_RUB = 7700  # лимит в рублях

# --- ОТПРАВКА В TELEGRAM ---
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": USER_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

# --- ПРОВЕРКА WildBerries ---
def check_wb():
    print("=== Проверка WildBerries ===")
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "123585351",  # Москва, всегда есть товары
        "query": "samsung a06",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
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

            if "a06" in name.lower() and price_rub <= PRICE_LIMIT_RUB:
                link = f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
                send_message(f"🔥 WildBerries: {name}\nЦена: {price_rub} ₽\nСсылка: {link}")
    except Exception as e:
        print(f"Ошибка WB: {e}")
        send_message(f"⚠ Ошибка WB: {e}")

# --- ПРОВЕРКА Ozon ---
def check_ozon():
    print("=== Проверка Ozon ===")
    url = "https://api.ozon.ru/composer-api.bx/page/json/v2"
    params = {"url": "/search/?text=samsung%20a06"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        widget_states = data.get("widgetStates", {})
        found = False

        for key, value in widget_states.items():
            if "searchResultsV2" in key:
                try:
                    decoded = unquote(value)
                    products_data = json.loads(decoded)
                    items = products_data.get("items", [])
                    if not items:
                        continue
                    for item in items:
                        name = item.get("cellTrackingInfo", {}).get("product", {}).get("title", "")
                        price_rub = item.get("cellTrackingInfo", {}).get("product", {}).get("price", {}).get("price", 0)
                        print(f"Ozon: {name} — {price_rub} ₽")

                        if "a06" in name.lower() and price_rub <= PRICE_LIMIT_RUB:
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

# --- ЗАПУСК ---
if __name__ == "__main__":
    send_message(f"✅ Бот запущен. Лимит: {PRICE_LIMIT_RUB} ₽. Проверка каждые 2 минуты.")
    offset = 0
    while True:
        try:
            # Обработка входящих команд
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
            updates = requests.get(url, timeout=10).json()
            for update in updates.get("result", []):
                message = update.get("message")
                if message and message.get("text") == "/start":
                    send_message("✅ Бот работает!")
                offset = update['update_id'] + 1

            # Запуск проверок
            check_wb()
            check_ozon()

        except Exception as e:
            print(f"Общая ошибка: {e}")
            send_message(f"⚠ Общая ошибка: {e}")

        time.sleep(120)  # каждые 2 минуты
