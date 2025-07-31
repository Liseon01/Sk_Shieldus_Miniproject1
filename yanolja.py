import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import re

# --- 선택자(Selectors) 중앙 관리 ---
SELECTORS = {
    "search_input": "input[placeholder*='지역, 숙소명']",
    "date_button": "button[class*='calendarButton']",
    "guest_button": "button[class*='capacityButton']",
    "calendar_day_template": "//td[@role='button' and contains(@aria-label, '{date_str_formatted}')]",
    "calendar_confirm_button": "(//button[contains(., '확인')])[last()]",
    
    # 인원수 선택 모달
    "adult_plus_button": "//div[text()='성인']/following-sibling::div//button[contains(@class, 'increase')]",
    "adult_minus_button": "//div[text()='성인']/following-sibling::div//button[contains(@class, 'decrease')]",
    "adult_current_count": "//div[text()='성인']/following-sibling::div//div[contains(@class, 'count')]",
    "child_plus_button": "//div[text()='아동']/following-sibling::div//button[contains(@class, 'increase')]",
    "child_minus_button": "//div[text()='아동']/following-sibling::div//button[contains(@class, 'decrease')]",
    "child_current_count": "//div[text()='아동']/following-sibling::div//div[contains(@class, 'count')]",
    "child_age_select_button": "(//div[contains(@class, 'ChildrenAgesSelector_bodyChildrenItemAge') and text()='나이선택'])[last()]",
    "child_age_option": "//button[contains(@class, 'BottomSheetContentsSelect_cellInteractor') and text()='만 7세']",
    "guest_apply_button": "//button[span[contains(., '적용하기')]]",

    # --- (업데이트) 최종 결과 페이지 선택자 - 실제 HTML 구조에 맞게 수정 ---
    "list_item_container": "a[href*='place-site.yanolja.com/places/']",  # 숙소 링크
    "item_title": "p.typography-subtitle-16-bold",  # 숙소명
    "item_type": "p.text-text-neutral-sub.typography-body-12-regular",  # 숙소 유형
    "item_location": "span.line-clamp-1.text-start",  # 위치
    "item_rating": "span.typography-body-14-bold",  # 평점
    "item_price": "span.typography-subtitle-18-bold",  # 가격
    "accommodation_price": "div.flex.flex-1.flex-col.items-end.justify-end.pt-4 span.typography-subtitle-18-bold",  # 숙박 가격
    "room_info": "div.flex.flex-col.gap-6.rounded-8.bg-fill-neutral-weak.px-8.py-8",  # 객실 정보
    "room_type": "span.line-clamp-1.text-start.text-text-neutral-sub.typography-body-12-regular",  # 객실 타입
}

def setup_driver():
    """안정성이 강화된 Selenium WebDriver를 설정하고 반환합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_experimental_option("detach", True)  # 브라우저 자동 닫기 위해 주석 처리
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    return driver

def js_click(driver, element):
    """자바스크립트를 이용해 요소를 클릭합니다."""
    driver.execute_script("arguments[0].click();", element)

def execute_search_flow(driver, wait, search_query, check_in_date, check_out_date, adults, children):
    """사용자가 요청한 순서대로 필터를 적용하고 검색을 실행합니다."""
    # (이전과 동일하여 주석 처리로 요약)
    try:
        # --- ① 검색어 입력 ---
        print("\n--- 1. 검색어 입력 ---")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["search_input"])))
        js_click(driver, search_box); search_box.clear(); search_box.send_keys(search_query)
        time.sleep(1)

        # --- ② 날짜 설정 ---
        print("\n--- 2. 날짜 설정 ---")
        date_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["date_button"])))
        js_click(driver, date_button)
        wait.until(EC.visibility_of_element_located((By.XPATH, SELECTORS["calendar_confirm_button"])))
        check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out_date, '%Y-%m-%d')
        check_in_formatted = f"{check_in_dt.year}년 {check_in_dt.month}월 {check_in_dt.day}일"
        check_out_formatted = f"{check_out_dt.year}년 {check_out_dt.month}월 {check_out_dt.day}일"
        check_in_selector = SELECTORS["calendar_day_template"].format(date_str_formatted=check_in_formatted)
        check_in_element = wait.until(EC.element_to_be_clickable((By.XPATH, check_in_selector)))
        js_click(driver, check_in_element)
        time.sleep(0.5)
        check_out_selector = SELECTORS["calendar_day_template"].format(date_str_formatted=check_out_formatted)
        check_out_element = wait.until(EC.element_to_be_clickable((By.XPATH, check_out_selector)))
        js_click(driver, check_out_element)
        confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["calendar_confirm_button"])))
        driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
        time.sleep(1)
        js_click(driver, confirm_button)
        print("날짜 '확인' 버튼 클릭 완료.")
        time.sleep(1)

        # --- ③ 인원 설정 ---
        print("\n--- 3. 인원 설정 ---")
        guest_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["guest_button"])))
        js_click(driver, guest_button)
        wait.until(EC.visibility_of_element_located((By.XPATH, SELECTORS["guest_apply_button"])))
        
        # 성인 인원수 조절
        current_adult_element = wait.until(EC.visibility_of_element_located((By.XPATH, SELECTORS["adult_current_count"])))
        current_adults = int(current_adult_element.text)
        adult_plus_button = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["adult_plus_button"])))
        adult_minus_button = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["adult_minus_button"])))
        while current_adults < adults:
            js_click(driver, adult_plus_button); current_adults += 1; time.sleep(0.3)
        while current_adults > adults:
            js_click(driver, adult_minus_button); current_adults -= 1; time.sleep(0.3)
        print(f"성인 {adults}명 설정 완료.")
            
        # 아동 인원수 및 나이 조절
        current_child_element = wait.until(EC.visibility_of_element_located((By.XPATH, SELECTORS["child_current_count"])))
        current_children = int(current_child_element.text)
        child_plus_button = driver.find_element(By.XPATH, SELECTORS["child_plus_button"])
        while current_children < children:
            js_click(driver, child_plus_button); current_children += 1; time.sleep(0.5)
            age_select_button = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["child_age_select_button"])))
            js_click(driver, age_select_button)
            time.sleep(0.5)
            age_option = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["child_age_option"])))
            js_click(driver, age_option)
            time.sleep(0.3)
        print(f"아동 {children}명 (만 7세) 설정 완료.")

        apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["guest_apply_button"])))
        js_click(driver, apply_button)
        print("인원 '적용하기' 버튼 클릭 완료.")
        time.sleep(1)

        # --- ④ 엔터(Enter) 키로 최종 검색 실행 ---
        print("\n--- 4. 최종 검색 실행 (Enter) ---")
        search_box = driver.find_element(By.CSS_SELECTOR, SELECTORS["search_input"])
        search_box.send_keys(Keys.ENTER)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["list_item_container"])))
        print("검색 결과 페이지 로딩 완료.")
        return True
        
    except Exception as e:
        print(f"필터 적용 및 검색 실행 중 오류 발생: {e}")
        return False

def crawl_accommodation_data(driver):
    """(핵심 수정) 페이지를 스크롤하며 객실별 상세 정보를 추출합니다."""
    print("\n--- 5. 데이터 추출 시작 ---")
    try:
        # 스크롤 다운
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5): # 스크롤 5번
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("페이지 끝까지 스크롤 완료.")
                break
            last_height = new_height
        
        # 모든 숙소 아이템 찾기
        items = driver.find_elements(By.CSS_SELECTOR, SELECTORS["list_item_container"])
        print(f"총 {len(items)}개의 숙소 정보를 찾았습니다.")
        
        results = []
        for idx, item in enumerate(items):
            try:
                # 기본 숙소 정보 추출
                try:
                    name_element = item.find_element(By.CSS_SELECTOR, SELECTORS["item_title"])
                    name = name_element.text.strip()
                except NoSuchElementException:
                    name = "N/A"
                
                # 숙소유형
                try:
                    type_elements = item.find_elements(By.CSS_SELECTOR, SELECTORS["item_type"])
                    category = type_elements[0].text.strip() if type_elements else "N/A"
                except NoSuchElementException:
                    category = "N/A"
                    
                # 위치
                try:
                    location_element = item.find_element(By.CSS_SELECTOR, SELECTORS["item_location"])
                    location = location_element.text.strip()
                except NoSuchElementException:
                    location = "N/A"
                    
                # 평점 (10점 만점으로 변환)
                try:
                    rating_elements = item.find_elements(By.CSS_SELECTOR, SELECTORS["item_rating"])
                    if rating_elements:
                        rating_text = rating_elements[0].text.strip()
                        rating_match = re.search(r'(\d+\.\d+)', rating_text)
                        if rating_match:
                            # 5점 만점을 10점 만점으로 변환
                            rating_5point = float(rating_match.group(1))
                            rating_10point = rating_5point * 2
                            rating = f"{rating_10point:.1f}"
                        else:
                            rating = rating_text
                    else:
                        rating = "평점 없음"
                except NoSuchElementException:
                    rating = "평점 없음"
                
                # 객실별 가격 정보 추출 (1박 기준으로 개선)
                room_prices = []
                
                # 1. 먼저 기본 가격 정보 추출 (1박 기준)
                try:
                    # 메인 가격 정보 찾기 (1박 기준)
                    price_elements = item.find_elements(By.CSS_SELECTOR, SELECTORS["item_price"])
                    base_price = "가격 정보 없음"
                    price_type = "1박 기준"
                    
                    for price_element in price_elements:
                        price_text = price_element.text.strip()
                        # "원" 제거하고 숫자만 추출
                        price_numbers = re.findall(r'[\d,]+', price_text)
                        if price_numbers:
                            # 쉼표 제거하고 숫자만 추출
                            clean_price = price_numbers[0].replace(',', '')
                            if clean_price.isdigit():
                                base_price = clean_price
                                price_type = "1박 기준"
                                break
                    
                    # 2. 객실별 상세 정보 추출
                    try:
                        # 객실 상세 정보가 있는 섹션 찾기
                        room_detail_sections = item.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.gap-6.rounded-8.bg-fill-neutral-weak.px-8.py-8")
                        
                        for room_section in room_detail_sections:
                            try:
                                # 객실 설명 텍스트 찾기
                                room_desc_elements = room_section.find_elements(By.CSS_SELECTOR, "span.line-clamp-1.text-start.text-text-neutral-sub.typography-body-12-regular")
                                
                                if room_desc_elements:
                                    room_desc = room_desc_elements[0].text.strip()
                                    
                                    # 인원수 추출 (객실 설명에서)
                                    capacity = "2인실"  # 기본값
                                    if "1인" in room_desc or "싱글" in room_desc:
                                        capacity = "1인실"
                                    elif "2인" in room_desc or "더블" in room_desc:
                                        capacity = "2인실"
                                    elif "3인" in room_desc or "트리플" in room_desc:
                                        capacity = "3인실"
                                    elif "4인" in room_desc or "쿼드" in room_desc:
                                        capacity = "4인실"
                                    elif "5인" in room_desc:
                                        capacity = "5인실"
                                    elif "6인" in room_desc:
                                        capacity = "6인실"
                                    
                                    # 객실 타입 결정
                                    room_type = room_desc[:30] if len(room_desc) > 30 else room_desc
                                    if not room_type or room_type == "":
                                        room_type = "기본객실"
                                    
                                    # 객실별 가격 정보 찾기
                                    room_price = base_price  # 기본값으로 메인 가격 사용
                                    room_price_type = price_type
                                    
                                    # 객실 섹션 내에서 가격 정보 찾기
                                    try:
                                        room_price_elements = room_section.find_elements(By.CSS_SELECTOR, "span.typography-subtitle-18-bold")
                                        for price_el in room_price_elements:
                                            price_text = price_el.text.strip()
                                            price_numbers = re.findall(r'[\d,]+', price_text)
                                            if price_numbers:
                                                clean_price = price_numbers[0].replace(',', '')
                                                if clean_price.isdigit():
                                                    room_price = clean_price
                                                    room_price_type = "1박 기준"
                                                    break
                                    except:
                                        pass
                                    
                                    room_prices.append({
                                        '객실타입': room_type,
                                        '인원수': capacity,
                                        '가격': room_price,
                                        '가격유형': room_price_type
                                    })
                                    
                            except Exception as e:
                                print(f"객실 상세 정보 추출 중 오류: {e}")
                                continue
                                
                    except Exception as e:
                        print(f"객실 섹션 찾기 중 오류: {e}")
                    
                    # 3. 객실 정보가 없으면 기본 가격 정보만 사용
                    if not room_prices:
                        # 예약 상태 확인
                        status_elements = item.find_elements(By.XPATH, ".//*[contains(text(), '예약마감') or contains(text(), '판매가') or contains(text(), '매진')]")
                        if status_elements:
                            base_price = "예약마감"
                            price_type = "예약마감"
                        
                        room_prices.append({
                            '객실타입': '기본객실',
                            '인원수': '2인실',
                            '가격': base_price,
                            '가격유형': price_type
                        })
                        
                except Exception as e:
                    print(f"가격 추출 중 오류: {e}")
                    room_prices.append({
                        '객실타입': '기본객실',
                        '인원수': '2인실',
                        '가격': '가격 정보 없음',
                        '가격유형': '오류'
                    })
                
                # 각 객실별로 결과 저장
                for room_info in room_prices:
                    results.append({
                        '숙소명': name,
                        '숙소유형': category,
                        '위치': location,
                        '평점': rating,
                        '가격': room_info['가격']
                    })
                
                print(f"[{idx+1}] {name} - {category} - {rating} - {len(room_prices)}개 객실")
                
            except Exception as e:
                print(f"항목 {idx+1} 처리 중 오류: {e}")
                continue
        
        return results
    except Exception as e:
        print(f"데이터 추출 중 오류 발생: {e}")
        return []

def main():
    """메인 실행 함수"""
    # === 검색하고 싶은 조건으로 변경하세요 ===
    search_query = "고양"
    check_in_date = "2025-08-12"
    check_out_date = "2025-08-14"
    adults = 2
    children = 1
    # ==================================

    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        start_url = "https://nol.yanolja.com/search?tab=place"
        
        driver.get(start_url)
        print(f"시작 URL 접속: {start_url}")
        
        if execute_search_flow(driver, wait, search_query, check_in_date, check_out_date, adults, children):
            scraped_data = crawl_accommodation_data(driver)
            if scraped_data:
                # pandas DataFrame으로 변환하여 표 형태로 출력
                df = pd.DataFrame(scraped_data)
                print(f"\n[최종 결과] 총 {len(df)}개의 숙소 정보 수집 완료")
                print(df)
                
                # CSV 파일로 저장
                filename = f"yanolja_{search_query}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"\n'{filename}' 파일로 저장되었습니다.")
            else:
                print("\n수집된 데이터가 없습니다.")
    except Exception as e:
        print(f"전체 과정에서 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()
        print("\n스크립트 실행 완료. 브라우저가 닫혔습니다.")

if __name__ == "__main__":
    main()
    