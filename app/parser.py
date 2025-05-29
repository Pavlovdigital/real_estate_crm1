import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from app import create_app, db
from app.models import Property

KRISHA_URL = 'https://krisha.kz/prodazha/kvartiry/petropavlovsk/?das[novostroiki]=1&das[who]=1'
OLX_URL = 'https://www.olx.kz/nedvizhimost/prodazha-kvartiry/petropavlovsk/?search%5Bfilter_enum_tipsobstvennosti%5D%5B0%5D=ot_hozyaina'

# --- Чтение справочников из JSON ---
_CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
_OPTIONS_DIR = os.path.join(_CURRENT_DIR, 'options')

def load_options_json(filename):
    file_path = os.path.join(_OPTIONS_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            opts = json.load(f)
            if isinstance(opts, list):
                return [x['name'] if isinstance(x, dict) and 'name' in x else x for x in opts]
            return []
    except FileNotFoundError:
        print(f"Error: JSON options file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return []

district_options = load_options_json('Район-options.json')
status_options = load_options_json('Статус-options.json') # Assuming 'Статус-options.json' also exists in app/options/
cat_options = load_options_json('КАТ-options.json') # Assuming 'КАТ-options.json' also exists in app/options/
plan_options = load_options_json('План-options.json') # Assuming 'План-options.json' also exists in app/options/
m_options = load_options_json('М-options.json') # Assuming 'М-options.json' also exists in app/options/
blkn_options = load_options_json('Блкн-options.json') # Assuming 'Блкн-options.json' also exists in app/options/
p_options = load_options_json('П-options.json') # Assuming 'П-options.json' also exists in app/options/
condition_options = load_options_json('Состояние-options.json') # Assuming 'Состояние-options.json' also exists in app/options/

def map_option(val, options):
    if not val: return ""
    for opt in options:
        if opt and opt.lower() in str(val).lower():
            return opt
    return val

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def parse_krisha(status=None):
    driver = get_driver()
    driver.get(KRISHA_URL)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = ['https://krisha.kz' + a['href'] for a in soup.select('.a-search-item__title')]
    total = len(links)
    for idx, url in enumerate(links):
        try:
            driver.get(url)
            time.sleep(2)
            s = BeautifulSoup(driver.page_source, 'html.parser')
            # Примерные извлечения:
            try:
                phone_btn = driver.find_element(By.CSS_SELECTOR, ".a-search-phone")
                phone_btn.click()
                time.sleep(1)
                phone = driver.find_element(By.CSS_SELECTOR, ".a-search-phone__popup-number").text.strip()
            except Exception:
                phone = ""
            external_id = url.split('/')[-2]
            title = s.select_one('h1').text.strip() if s.select_one('h1') else ''
            price = s.select_one('.a-search-item__price').text.replace('₸', '').replace(' ', '').strip() if s.select_one('.a-search-item__price') else ''
            description = s.select_one('.a-search-item__description').text.strip() if s.select_one('.a-search-item__description') else ''
            photos = ','.join([img['src'] for img in s.select('.a-search-photo img') if img.has_attr('src')])
            # --- ВАЖНО: здесь подставляй поля из JSON! ---
            district = map_option(title, district_options)
            status_val = "Активен" # Или парсь с сайта
            cat = map_option("Продажа", cat_options)
            plan = map_option("", plan_options)
            m_val = map_option("", m_options)
            blkn_val = map_option("", blkn_options)
            p_val = map_option("", p_options)
            cond = map_option("", condition_options)
            street = ""  # Если найдёшь
            d_kv = ""
            year = ""
            s_val = ""
            s_kh = ""
            # ---

            # Проверка дублей
            exists = Property.query.filter_by(external_id=external_id).first()
            if exists:
                exists.phone = phone
                exists.price = float(price) if price.replace('.', '', 1).isdigit() else None
                exists.photos = photos
                exists.district = district
                exists.status = status_val
                exists.cat = cat
                db.session.commit()
                msg = f'[KRISHA] Обновлен {external_id}'
            else:
                prop = Property(
                    cat=cat,
                    status=status_val,
                    district=district,
                    price=float(price) if price.replace('.', '', 1).isdigit() else None,
                    plan=plan,
                    floor=None,
                    total_floors=None,
                    area=None,
                    m=m_val,
                    s=s_val,
                    s_kh=s_kh,
                    blkn=blkn_val,
                    p=p_val,
                    condition=cond,
                    phone=phone,
                    street=street,
                    d_kv=d_kv,
                    year=year,
                    description=description,
                    photos=photos,
                    link=url,
                    external_id=external_id,
                    source='krisha'
                )
                db.session.add(prop)
                db.session.commit()
                msg = f'[KRISHA] Добавлен {external_id}'
        except Exception as e:
            msg = f"[KRISHA] Ошибка парсинга {url}: {e}"
        if status is not None:
            status["step"] = f"Krisha: {idx+1}/{total}"
            status["percent"] = int(50 * (idx + 1) / total)
            status["log"].append(msg)
    driver.quit()

def parse_olx(status=None):
    driver = get_driver()
    driver.get(OLX_URL)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = [a['href'] if a['href'].startswith('http') else 'https://www.olx.kz'+a['href'] for a in soup.select('a.css-rc5s2u')]
    total = len(links)
    for idx, url in enumerate(links):
        try:
            driver.get(url)
            time.sleep(2)
            s = BeautifulSoup(driver.page_source, 'html.parser')
            try:
                phone_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="ad-contact-phone-reveal"]')
                phone_btn.click()
                time.sleep(1)
                phone = driver.find_element(By.CSS_SELECTOR, 'a[data-cy="ad-contact-phone"]').text.strip()
            except Exception:
                phone = ''
            external_id = url.split('-')[-1].replace('.html', '')
            title = s.select_one('h1').text.strip() if s.select_one('h1') else ''
            price = s.select_one('h3[data-testid="ad-price"]').text.replace('₸', '').replace(' ', '').strip() if s.select_one('h3[data-testid="ad-price"]') else ''
            description = s.select_one('[data-cy="ad_description"]').text.strip() if s.select_one('[data-cy="ad_description"]') else ''
            photos = ','.join([img['src'] for img in s.select('.swiper-zoom-container img') if img.has_attr('src')])

            district = map_option(title, district_options)
            status_val = "Активен"
            cat = map_option("Продажа", cat_options)
            plan = map_option("", plan_options)
            m_val = map_option("", m_options)
            blkn_val = map_option("", blkn_options)
            p_val = map_option("", p_options)
            cond = map_option("", condition_options)
            street = ""  # Если найдёшь
            d_kv = ""
            year = ""
            s_val = ""
            s_kh = ""

            exists = Property.query.filter_by(external_id=external_id).first()
            if exists:
                exists.phone = phone
                exists.price = float(price) if price.replace('.', '', 1).isdigit() else None
                exists.photos = photos
                exists.district = district
                exists.status = status_val
                exists.cat = cat
                db.session.commit()
                msg = f'[OLX] Обновлен {external_id}'
            else:
                prop = Property(
                    cat=cat,
                    status=status_val,
                    district=district,
                    price=float(price) if price.replace('.', '', 1).isdigit() else None,
                    plan=plan,
                    floor=None,
                    total_floors=None,
                    area=None,
                    m=m_val,
                    s=s_val,
                    s_kh=s_kh,
                    blkn=blkn_val,
                    p=p_val,
                    condition=cond,
                    phone=phone,
                    street=street,
                    d_kv=d_kv,
                    year=year,
                    description=description,
                    photos=photos,
                    link=url,
                    external_id=external_id,
                    source='olx'
                )
                db.session.add(prop)
                db.session.commit()
                msg = f'[OLX] Добавлен {external_id}'
        except Exception as e:
            msg = f"[OLX] Ошибка парсинга {url}: {e}"
        if status is not None:
            status["step"] = f"OLX: {idx+1}/{total}"
            status["percent"] = 50 + int(50 * (idx + 1) / total)
            status["log"].append(msg)
    driver.quit()

# Для standalone-запуска:
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        parse_krisha()
        parse_olx()
