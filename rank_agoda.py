import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_korean_destinations_headless():
    """
    브라우저 창을 띄우지 않는 헤드리스 모드에서
    Agoda의 '대한민국' 인기 여행지만 필터링하여 스크래핑합니다.
    """
    # 대한민국 인기 여행지 정보를 담고 있는 공식 URL
    url = "https://www.agoda.com/ko-kr/?site_id=1922887&tag=eeeb2a37-a3e0-4932-8325-55d6a8ba95a4&gad_source=1&gad_campaignid=21035050206&gbraid=0AAAAAD-GdVm-Ra4Jt2RO12K4rpJGOB6Ar&device=c&network=g&adid=734266400825&rand=6452377490732081213&expid=&adpos=&aud=kwd-304551434341&gclid=Cj0KCQjwhafEBhCcARIsAEGZEKJgxPYw3oBOYAsk3-MX2LXPv554ReM-NAbORHlFUFGF5dFaw7L7Y00aAocPEALw_wcB&checkIn=2025-08-08&checkOut=2025-08-09&adults=2&rooms=1&pslc=1&ds=O09z9flHLUXMHZ%2FO"
    
    try:
        print("▶ Selenium 웹 드라이버를 설정합니다 (헤드리스 모드)...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # --- 이 부분이 수정되었습니다! ---
        # 브라우저 창을 띄우지 않는 헤드리스(headless) 모드 설정
        options.add_argument("--headless=new")
        
        driver = webdriver.Chrome(service=service, options=options)
        
        wait = WebDriverWait(driver, 20)

        print(f"▶ '{url}' 페이지로 이동합니다...")
        driver.get(url)

        # 쿠키 동의 팝업 처리
        try:
            print("▷ 쿠키 동의 팝업을 확인합니다...")
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="모두 동의"]'))
            )
            cookie_button.click()
            print("    ✔ 쿠키 팝업을 닫았습니다.")
        except TimeoutException:
            print("    - 쿠키 팝업이 발견되지 않았습니다.")

        # '국내' 여행지 목록이 나타날 때까지 대기
        print("▷ '대한민국' 인기 여행지 목록이 로드될 때까지 대기합니다...")
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-element-type='domestic']"))
        )
        print("    ✔ '대한민국' 인기 여행지 목록을 찾았습니다!")
        
        # 데이터 스크래핑
        print("▶ 데이터 스크래핑을 시작합니다...")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # 'domestic' 타입의 여행지 카드만 선택
        destination_cards = soup.select("div[data-element-type='domestic']")
        
        scraped_data = []
        for card in destination_cards:
            city_tag = card.select_one("h3[data-testid='destination-card-city-name']")
            city = city_tag.text.strip() if city_tag else '이름 없음'
            
            count_tag = card.find('span', string=re.compile(r'숙소'))
            count = '0'
            if count_tag and (match := re.search(r'[\d,]+', count_tag.text)):
                count = match.group(0)

            scraped_data.append({'여행지': city, '숙소 수': count})

        # 결과 저장
        df = pd.DataFrame(scraped_data)
        file_name = 'agoada_recommend.csv'
        df.to_csv(file_name, index=False, encoding='utf-8-sig')

        print(f"\n✅ 스크래핑 성공! '{file_name}' 파일이 저장되었습니다.")
        print("\n--- 스크래핑 결과 (대한민국) ---")
        print(df)

    except TimeoutException:
        print("\n❌ 오류: 시간 초과. 웹페이지에서 원하는 정보를 찾지 못했습니다.")
        print("    'error_screenshot.png' 파일에 현재 화면을 저장했습니다. 확인해보세요.")
    except Exception as e:
        print(f"\n❌ 알 수 없는 오류가 발생했습니다: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("\n▶ 웹 드라이버를 종료했습니다.")

if __name__ == '__main__':
    scrape_korean_destinations_headless()