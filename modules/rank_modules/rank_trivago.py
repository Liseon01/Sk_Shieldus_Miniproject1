from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def get_trivago_destinations():
    """
    Trivago 인기 목적지를 헤드리스 모드로 크롤링하여 리스트로 반환.
    """
    # 브라우저 옵션 설정
    options = Options()
    options.add_argument('--headless')  # 헤드리스 모드 활성화
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('window-size=600,700')
    # 헤드리스 브라우저임을 감지하지 못하도록 User-Agent 설정
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')


    # 드라이버 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Trivago 접속
        driver.get("https://www.trivago.co.kr/")
        wait = WebDriverWait(driver, 15)

        # 인기 목적지 열기
        search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="search-form-destination"]')))
        search_btn.click()

        # 인기 목적지 로딩 대기
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="apd-destination-button"]')))
        time.sleep(1) # 동적 콘텐츠 로딩을 위해 잠시 대기

        # 페이지 소스 가져오기
        html = driver.page_source
    finally:
        driver.quit()

    # BeautifulSoup 파싱
    soup = BeautifulSoup(html, 'html.parser')
    buttons = soup.select('button[data-testid="apd-destination-button"]')

    # 지역 이름 추출 및 중복 제거
    regions = [btn.get_text(strip=True) for btn in buttons if btn.get_text(strip=True)]
    unique_regions = list(dict.fromkeys(regions))  # 순서 유지하며 중복 제거

    return unique_regions

if __name__ == "__main__":
    destinations = get_trivago_destinations()
    print("✈️ Trivago 인기 여행지 TOP:", len(destinations))
    for i, region in enumerate(destinations, start=1):
        print(f"{i}위: {region}")