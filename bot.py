import requests
import time
import os
import json
from bs4 import BeautifulSoup

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменных окружения
USER_ID = int(os.getenv("USER_ID"))  # Твой Telegram user_id
PRICE_LIMIT_AMD = 36000
AMD_TO_RUB = 0.18  # Примерный курс (1 драм = 0.18 руб.)

# --- ФУНКЦИИ ДЛЯ ОТПРАВКИ ---
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": USER_ID, "text": text}
    requests.post(url, data=data)

# --- ОБРАБОТКА КОМАНД ---
def handle_command(message):
    if not message:
        return
    text = message.get('text')
    if text == "/start":
        send_message("✅ Бот запущен и работает!")

# --- ПРОВЕРКА WildBerries через API ---
def check_wb():
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
        r = requests.get(search_url, params=params)
        data = r.json()
        products = data.get("data", {}).get("products", [])
        for product in products:
            name = product.get("name", "")
            price_rub = product.get("salePriceU", 0) / 100  # в API цена в копейках
            price_amd = int(price_rub / AMD_TO_RUB)

            if "a06" in name.lower() and price_amd < PRICE_LIMIT_AMD:
                link = f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
                send_message(f"🔥 WildBerries: {name}\nЦена: {price_amd} драм\nСсылка: {link}")
    except Exception as e:
        send_message(f"⚠ Ошибка WB: {e}")

# --- ПРОВЕРКА Ozon через JSON ---
def check_ozon():
    search_url = "https://www.ozon.ru/search/?from_global=true&text=samsung%20a06"
    try:
        r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        scripts = soup.find_all("script")

        for script in scripts:
            if "searchResultsV2" in script.text:
                try:
                    json_text = script.text.strip()
                    start = json_text.find('{')
                    end = json_text.rfind('}') + 1
                    data = json.loads(json_text[start:end])
                    items = data.get("searchResultsV2", {}).get("items", [])

                    for item in items:
                        name = item.get("cellTrackingInfo", {}).get("product", {}).get("title", "")
                        price_rub = item.get("cellTrackingInfo", {}).get("product", {}).get("price", {}).get("price", 0)
                        price_amd = int(price_rub / AMD_TO_RUB)

                        if "a06" in name.lower() and price_amd < PRICE_LIMIT_AMD:
                            link = "https://www.ozon.ru" + item.get("link", "")
                            send_message(f"🔥 Ozon: {name}\nЦена: {price_amd} драм\nСсылка: {link}")
                except Exception:
                    continue
    except Exception as e:
        send_message(f"⚠ Ошибка Ozon: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    send_message(f"✅ Бот запущен. Лимит: {PRICE_LIMIT_AMD} драм. Проверка каждые 2 минуты.")
    offset = 0
    while True:
        try:
            # Проверка команд
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
            response = requests.get(url).json()

            for update in response.get('result', []):
                handle_command(update.get('message'))
                offset = update['update_id'] + 1

            # Проверка цен
            check_wb()
            check_ozon()

        except Exception as e:
            send_message(f"⚠ Общая ошибка: {e}")

        time.sleep(120)  # каждые 2 минуты

