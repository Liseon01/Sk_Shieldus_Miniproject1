import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

def scrape_korean_destinations_headless():
    """
    Agoda의 '대한민국' 인기 여행지를 크롤링하여 리스트로 반환.
    """
    url = "https://www.agoda.com/ko-kr/?checkIn=2025-08-08&checkOut=2025-08-09&adults=2&rooms=1&pslc=1"

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    destinations = []

    try:
        print("▶ Agoda 접속 중...")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # 쿠키 팝업 처리
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="모두 동의"]'))
            )
            cookie_button.click()
        except TimeoutException:
            pass  # 쿠키 팝업이 없을 수 있음

        # '국내' 여행지 목록이 나타날 때까지 대기
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-element-type='domestic']"))
        )

        # HTML 파싱
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        destination_cards = soup.select("div[data-element-type='domestic']")

        for card in destination_cards:
            city_tag = card.select_one("h3[data-testid='destination-card-city-name']")
            city = city_tag.text.strip() if city_tag else None
            if city:
                destinations.append(city)

    except Exception as e:
        print(f"❌ Agoda 스크래핑 오류: {e}")
    finally:
        driver.quit()

    return destinations

if __name__ == "__main__":
    results = scrape_korean_destinations_headless()
    print("🏨 Agoda 인기 여행지:")
    for i, city in enumerate(results, 1):
        print(f"{i}위: {city}")
