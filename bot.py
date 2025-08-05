import requests
import time
from bs4 import BeautifulSoup
import os

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменных окружения
USER_ID = int(os.getenv("USER_ID"))  # Твой Telegram user_id
PRICE_LIMIT_AMD = 30000
AMD_TO_RUB = 0.18  # Примерный курс (1 драм = 0.18 руб.), можно сделать автообновление

# --- ФУНКЦИИ ДЛЯ ОТПРАВКИ ---
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": USER_ID, "text": text}
    requests.post(url, data=data)

# --- ОБРАБОТКА КОМАНД ---
def handle_command(message):
    text = message.get('text')
    if text == "/start":
        send_message("✅ Бот запущен и работает!")

# --- ПРОВЕРКА ЦЕН ---
def check_wb():
    search_url = "https://www.wildberries.ru/catalog/0/search.aspx?search=samsung%20a06"
    r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.product-card__wrapper")

    for item in items:
        name = item.select_one("span.goods-name").text.strip() if item.select_one("span.goods-name") else ""
        price_tag = item.select_one("ins.price__lower-price")
        if not price_tag:
            continue
        price_rub = int(price_tag.text.replace("₽", "").replace(" ", "").strip())
        price_amd = int(price_rub / AMD_TO_RUB)

        if "a06" in name.lower():
            if price_amd < PRICE_LIMIT_AMD:
                link_tag = item.find_parent("a")
                link = "https://www.wildberries.ru" + link_tag["href"] if link_tag else search_url
                send_message(f"🔥 WildBerries: {name}\nЦена: {price_amd} драм\nСсылка: {link}")

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
        price_rub = int(price_tag.text.replace("₽", "").replace(" ", "").strip())
        price_amd = int(price_rub / AMD_TO_RUB)

        if "a06" in name.lower():
            link_tag = item.find_parent("a")
            link = "https://www.ozon.ru" + link_tag["href"] if link_tag else search_url
            if price_amd < PRICE_LIMIT_AMD:
                send_message(f"🔥 Ozon: {name}\nЦена: {price_amd} драм\nСсылка: {link}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    send_message("✅ Бот запущен и проверяет цены Samsung A06 каждые 15 минут.")
    
    # Получаем обновления от бота (polling)
    offset = 0
    while True:
        try:
            # Получаем последние обновления
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
            response = requests.get(url).json()
            
            for update in response.get('result', []):
                handle_command(update.get('message'))
                offset = update['update_id'] + 1  # Обновляем offset, чтобы не получать одни и те же обновления

            check_wb()
            check_ozon()
            
        except Exception as e:
            send_message(f"⚠ Ошибка: {e}")
        
        time.sleep(5)  # Пауза в 5 секунд перед следующим запросом
