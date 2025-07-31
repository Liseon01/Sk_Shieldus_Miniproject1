import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# 크롬 옵션 설정 (헤드리스 모드)
options = Options()
options.add_argument("--headless=new")  
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.yeogi.com/")
time.sleep(3)

# 인기 검색 키워드 섹션 범위 지정
popular_section = driver.find_element(By.CSS_SELECTOR, 'section[aria-label="인기 검색 키워드"]')

# 해당 섹션 내부에서만 검색어 추출
keyword_elements = popular_section.find_elements(
    By.CSS_SELECTOR,
    'div.css-grswmc > a'
)

# 결과 저장 리스트
results = []
for i, el in enumerate(keyword_elements, 1):
    keyword = el.text.strip()
    results.append([i, keyword])

# CSV 파일로 저장
with open("rank_yeogi.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file)
    writer.writerow(["순위", "키워드"])  
    writer.writerows(results)
    print("저장 완료")

driver.quit()