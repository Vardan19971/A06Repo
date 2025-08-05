import requests
import time
import os

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен бота
USER_ID = int(os.getenv("USER_ID"))  # Твой Telegram ID
PRICE_LIMIT_AMD = 36000
AMD_TO_RUB = 0.18  # Примерный курс

# --- ОТПРАВКА В TELEGRAM ---
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": USER_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

# --- ПРОВЕРКА WildBerries ---
def check_wb():
    print("=== Проверка WildBerries ===")
    search_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "query": "samsung a06",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
    }
    try:
        r = requests.get(search_url, params=params, timeout=10)
        products = r.json().get("data", {}).get("products", [])
        for product in products:
            name = product.get("name", "")
            price_rub = product.get("salePriceU", 0) / 100
            price_amd = int(price_rub / AMD_TO_RUB)
            print(f"WB: {name} — {price_amd} драм")

            if "a06" in name.lower() and price_amd <= PRICE_LIMIT_AMD:
                link = f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
                send_message(f"🔥 WildBerries: {name}\nЦена: {price_amd} драм\nСсылка: {link}")
    except Exception as e:
        print(f"Ошибка WB: {e}")
        send_message(f"⚠ Ошибка WB: {e}")

# --- ПРОВЕРКА Ozon ---
def check_ozon():
    print("=== Проверка Ozon ===")
    search_url = "https://api.ozon.ru/composer-api.bx/page/json/v2"
    params = {"url": "/search/?text=samsung%20a06"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(search_url, params=params, headers=headers, timeout=10)
        data = r.json()
        items = data.get("widgetStates", {})
        
        # Вытаскиваем список товаров
        for key, value in items.items():
            if "searchResultsV2" in key:
                try:
                    products = requests.utils.unquote(value)
                    import json
                    products_json = json.loads(products)
                    for item in products_json.get("items", []):
                        product_info = item.get("cellTrackingInfo", {}).get("product", {})
                        name = product_info.get("title", "")
                        price_rub = product_info.get("price", {}).get("price", 0)
                        price_amd = int(price_rub / AMD_TO_RUB)
                        print(f"Ozon: {name} — {price_amd} драм")

                        if "a06" in name.lower() and price_amd <= PRICE_LIMIT_AMD:
                            link = "https://www.ozon.ru" + item.get("link", "")
                            send_message(f"🔥 Ozon: {name}\nЦена: {price_amd} драм\nСсылка: {link}")
                except Exception:
                    continue
    except Exception as e:
        print(f"Ошибка Ozon: {e}")
        send_message(f"⚠ Ошибка Ozon: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    send_message(f"✅ Бот запущен. Лимит: {PRICE_LIMIT_AMD} драм. Проверка каждые 2 минуты.")
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
