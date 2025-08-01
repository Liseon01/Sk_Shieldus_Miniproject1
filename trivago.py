import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import random
import re
from datetime import datetime

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def configure_driver():
    """웹 드라이버를 설정하는 함수"""
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2
    })
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080") 
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def crawl_trivago_final(search_query, check_in_date, check_out_date, num_adults):
    """
    트리바고에서 모든 페이지의 호텔 정보를 크롤링하는 최종 함수
    """
    driver = configure_driver()
    wait = WebDriverWait(driver, 15)
    scraped_results = []
    
    try:
        # --- 1. 검색 옵션 설정 ---
        print("트리바고 메인 페이지 접속 중...")
        driver.get("https://www.trivago.co.kr/")

        print(f"'{search_query}' 검색어 입력...")
        destination_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="search"]')))
        destination_input.clear()
        destination_input.send_keys(search_query)
        time.sleep(1)
        destination_input.send_keys(Keys.TAB)
        
        print(f"날짜 선택: 체크인({check_in_date}), 체크아웃({check_out_date})")
        
        try:
            current_dt = datetime.now()
            target_dt = datetime.strptime(check_in_date, "%Y-%m-%d")
            month_diff = (target_dt.year - current_dt.year) * 12 + (target_dt.month - current_dt.month)

            if month_diff > 0:
                print(f"'{target_dt.year}년 {target_dt.month}월'로 이동하기 위해 '다음 달' 버튼을 {month_diff}번 클릭합니다.")
                # ✅ [수정] for 루프 안에서 매번 '다음 달' 버튼을 새로 찾도록 변경
                for i in range(month_diff):
                    next_month_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="calendar-button-next"]')))
                    next_month_button.click()
                    print(f"  ({i+1}/{month_diff}) '다음 달' 클릭")
                    time.sleep(0.3)
        except Exception as e:
            print(f"달력 이동 중 오류 발생: {e}")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-testid="valid-calendar-day-{check_in_date}"]'))).click()
        time.sleep(0.5)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-testid="valid-calendar-day-{check_out_date}"]'))).click()
        
        print(f"인원수 선택: 성인 {num_adults}명")
        adults_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="adults-amount"]')))
        current_adults = int(adults_input.get_attribute('value'))
        
        if current_adults != num_adults:
            button_id = "adults-amount-plus-button" if current_adults < num_adults else "adults-amount-minus-button"
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-testid="{button_id}"]')))
            for _ in range(abs(num_adults - current_adults)):
                button.click()
                time.sleep(0.2)
        
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="guest-selector-apply"]'))).click()
        print("설정한 조건으로 검색 실행...")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="search-button-with-loader"]'))).click()

        # --- 2. 모든 검색 결과 페이지 순회하며 정보 추출 ---
        page_number = 1
        while True:
            print(f"\n--- {page_number} 페이지 스크레이핑 시작 ---")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="item"]')))
            time.sleep(2)

            first_hotel_on_page = driver.find_element(By.CSS_SELECTOR, 'article[data-testid="item"]')
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            hotel_cards = soup.select('article[data-testid="item"]')
            
            if not hotel_cards:
                print("현재 페이지에서 숙소 정보를 찾을 수 없습니다.")
                break

            print(f"{len(hotel_cards)}개의 숙소 정보를 추출합니다.")
            for card in hotel_cards:
                try:
                    name = card.select_one('span[itemprop="name"]').text.strip()
                    location = card.select_one('button[data-testid="distance-label-section"] span').text.strip()
                    rating = card.select_one('span[itemprop="ratingValue"]').text.strip()
                    type_element = card.select_one('button[data-testid="accommodation-type"]')
                    accommodation_type = type_element.text.strip() if type_element else "유형 정보 없음"
                    price_element = card.select_one('div[data-testid="recommended-price"]')
                    price = "가격 정보 없음"
                    if price_element:
                        price_match = re.search(r'[\d,]+', price_element.text.strip())
                        if price_match:
                            price = price_match.group(0) + "원"
                    scraped_results.append({
                        '숙소명': name, '숙소유형': accommodation_type, '위치': location,
                        '평점': rating, '가격': price,
                    })
                except AttributeError:
                    continue
            
            # --- 다음 페이지로 이동 ('다음' 화살표 버튼 클릭) ---
            try:
                next_page_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="next-result-page"]')
                
                if next_page_button.get_attribute('disabled'):
                    print("마지막 페이지입니다. 스크레이핑을 종료합니다.")
                    break
                    
                driver.execute_script("arguments[0].click();", next_page_button)
                page_number += 1
                print(f"다음 페이지({page_number} 페이지)로 이동합니다.")
                
                wait.until(EC.staleness_of(first_hotel_on_page))

            except NoSuchElementException:
                print("마지막 페이지입니다. 스크레이핑을 종료합니다.")
                break
    
    except Exception as e:
        print(f"크롤링 중 전반적인 오류 발생: {e}")
    finally:
        print("\n크롤링 종료. 브라우저를 닫습니다.")
        driver.quit()
        return scraped_results

# --- 메인 코드 실행 ---
if __name__ == "__main__":
    SEARCH_QUERY = "서울"
    CHECK_IN = "2025-11-20"
    CHECK_OUT = "2025-11-23"
    ADULTS = 2

    print(f"'{SEARCH_QUERY}' 지역, {CHECK_IN} ~ {CHECK_OUT}, 성인 {ADULTS}명 조건으로 크롤링 시작...")
    
    scraped_data = crawl_trivago_final(
        search_query=SEARCH_QUERY,
        check_in_date=CHECK_IN,
        check_out_date=CHECK_OUT,
        num_adults=ADULTS
    )

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        df = df[['숙소명', '숙소유형', '위치', '평점', '가격']]
        print(f"\n총 {len(df)}개의 숙소 정보를 찾았습니다.")
        print("\n" + "="*80)
        print(df)
        print("="*80)
        
        filename = f"trivago_{SEARCH_QUERY}_all_pages.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n'{filename}' 파일로 저장이 완료되었습니다.")
    else:
        print("트리바고에서 크롤링된 데이터가 없습니다.")