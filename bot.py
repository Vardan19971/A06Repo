import os
import time
import requests
from bs4 import BeautifulSoup

# Получаем токен и user_id из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = os.getenv("USER_ID")

PRICE_LIMIT_AMD = 30000
AMD_TO_RUB = 0.18  # примерный курс (1 драм = 0.18 руб.), можно заменить API-запросом

if not BOT_TOKEN or not USER_ID:
    raise ValueError("❌ Переменные окружения BOT_TOKEN и USER_ID должны быть заданы!")

# Отправка сообщения в Telegram
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": USER_ID, "text": text}
    requests.post(url, data=data)

# Проверка WildBerries
def check_wb():
    search_url = "https://www.wildberries.ru/catalog/0/search.aspx?search=samsung%20a06"
    r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.product-card__wrapper")

    for item in items:
        name = item.select_one("span.goods-name")
        if not name:
            continue
        name = name.text.strip()

        price_tag = item.select_one("ins.price__lower-price")
        if not price_tag:
            continue
        try:
            price_rub = int(price_tag.text.replace("₽", "").replace(" ", "").strip())
        except:
            continue

        price_amd = int(price_rub / AMD_TO_RUB)

        if "a06" in name.lower() and price_amd < PRICE_LIMIT_AMD:
            link_tag = item.find_parent("a")
            link = "https://www.wildberries.ru" + link_tag["href"] if link_tag else search_url
            send_message(f"🔥 WildBerries: {name}\nЦена: {price_amd} драм\nСсылка: {link}")

# Проверка Ozon
def check_ozon():
    search_url = "https://www.ozon.ru/search/?from_global=true&text=samsung%20a06"
    r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.tile-wrapper")

    for item in items:
        name_tag = item.select_one("span.tsBodyL")
        if not name_tag:
            continue
        name = name_tag.text.strip()

        price_tag = item.select_one("span.c301__price")
        if not price_tag:
            continue
        try:
            price_rub = int(price_tag.text.replace("₽", "").replace(" ", "").strip())
        except:
            continue

        price_amd = int(price_rub / AMD_TO_RUB)

        if "a06" in name.lower() and price_amd < PRICE_LIMIT_AMD:
            link_tag = item.find_parent("a")
            link = "https://www.ozon.ru" + link_tag["href"] if link_tag else search_url
            send_message(f"🔥 Ozon: {name}\nЦена: {price_amd} драм\nСсылка: {link}")

if name == "main":
    send_message("✅ Бот запущен и проверяет цены Samsung A06 каждые 15 минут.")
    while True:
        try:
            check_wb()
            check_ozon()
        except Exception as e:
            send_message(f"⚠ Ошибка: {e}")
        time.sleep(900)  # каждые 15 минут