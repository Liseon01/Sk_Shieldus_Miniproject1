from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time

# 브라우저 옵션 설정
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('window-size=600,700')

# 드라이버 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Trivago 접속
driver.get("https://www.trivago.co.kr/")
wait = WebDriverWait(driver, 15)

# 인기 목적지 열기
search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="search-form-destination"]')))
search_btn.click()

# 인기 목적지 로딩 대기
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="apd-destination-button"]')))
time.sleep(1)

# 페이지 소스 가져오기
html = driver.page_source
driver.quit()

# BeautifulSoup 파싱
soup = BeautifulSoup(html, 'html.parser')
buttons = soup.select('button[data-testid="apd-destination-button"]')

# 지역 이름 추출 및 중복 제거
regions = [btn.get_text(strip=True) for btn in buttons if btn.get_text(strip=True)]
unique_regions = list(dict.fromkeys(regions))  # 순서 유지하며 중복 제거

# CSV로 저장
with open("rank_trivago.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["순위", "지역명"])
    for i, region in enumerate(unique_regions, start=1):
        writer.writerow([i, region])

print("CSV 저장 완료 rank_trivago.csv")