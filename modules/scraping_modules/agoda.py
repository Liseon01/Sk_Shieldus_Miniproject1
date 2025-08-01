import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def select_date_in_calendar(driver, wait, date_str):
    """
    캘린더에서 다음 달로 이동하며 원하는 날짜를 선택하는 함수
    """
    for _ in range(12):
        try:
            date_element = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"span[data-selenium-date='{date_str}']")))
            driver.execute_script("arguments[0].click();", date_element)
            print(f"✅ '{date_str}' 날짜를 선택했습니다.")
            return True
        except TimeoutException:
            print("현재 달력에 원하는 날짜가 없어 다음 달로 이동합니다.")
            try:
                next_month_button = driver.find_element(By.CSS_SELECTOR, "div[data-selenium='calendar-next-month-button']")
                next_month_button.click()
                time.sleep(0.5)
            except NoSuchElementException:
                print("❌ '다음 달' 버튼을 찾을 수 없습니다.")
                return False

    print(f"❌ 12개월 내에서 '{date_str}' 날짜를 찾지 못했습니다.")
    return False


def scrape_agoda_final(destination, checkin_date, checkout_date, adults=2):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    print("아고다 웹사이트에 접속합니다...")
    driver.get("https://www.agoda.com/ko-kr/")
    driver.maximize_window()

    try:
        print(f"'{destination}' 입력 후 자동완성 창을 닫습니다...")
        search_box = wait.until(EC.visibility_of_element_located((By.ID, "textInput")))
        search_box.clear()
        search_box.send_keys(destination)
        time.sleep(1)
        search_box.send_keys(Keys.ESCAPE)

        print(f"캘린더를 열고 날짜({checkin_date} ~ {checkout_date})를 선택합니다...")
        checkin_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element-name='check-in-box']")))
        checkin_box.click()

        if not select_date_in_calendar(driver, wait, checkin_date): return None
        time.sleep(0.5)
        if not select_date_in_calendar(driver, wait, checkout_date): return None
        time.sleep(0.5)

        # ==================================================================
        # ## 인원수 설정 (최종 수정 버전) ##
        # ==================================================================
        print(f"성인 인원을 {adults}명으로 설정합니다...")
        try:
            add_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-selenium='plus'][data-element-name='occupancy-selector-panel-adult']")))
            subtract_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-selenium='minus'][data-element-name='occupancy-selector-panel-adult']")))

            current_adults_value = subtract_button.get_attribute('data-element-value')
            current_adults = int(current_adults_value) + 1
            print(f"현재 설정된 인원: {current_adults}명")

            # 인원수 조절 로직
            if adults > current_adults:
                for _ in range(adults - current_adults):
                    add_button.click()
                    time.sleep(0.2)
            elif adults < current_adults:
                for _ in range(current_adults - adults):
                    subtract_button.click()
                    time.sleep(0.2)

            print(f"✅ 성인 인원을 {adults}명으로 성공적으로 설정했습니다.")

        except TimeoutException:
            print("❌ 인원수 조절 버튼을 찾는 데 실패했습니다. CSS 선택자를 다시 확인해야 합니다.")
            driver.quit()
            return None

        # ==================================================================
        # ## 인원수 설정 종료 ##
        # ==================================================================

        print("검색 버튼을 클릭합니다...")
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-selenium='searchButton']")))
        search_button.click()

        print("검색 결과를 기다립니다...")
        time.sleep(40)

        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            print("✅ 페이지 로딩이 완료되었습니다.")
        except TimeoutException:
            print("⚠️ 페이지 로딩이 완료되지 않았지만 계속 진행합니다.")

        # 현재 URL 확인
        current_url = driver.current_url
        print(f"현재 URL: {current_url}")

        if "search" not in current_url.lower():
            print("❌ 검색 결과 페이지가 아닙니다. 다시 시도합니다.")
            driver.refresh()
            time.sleep(20)

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-selenium='hotel-name']")))
            print("✅ 호텔 이름 요소를 찾았습니다.")
        except TimeoutException:
            print("❌ 호텔 이름 요소를 찾지 못했습니다.")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("디버깅을 위해 'debug_page.html' 파일을 저장했습니다.")
            driver.quit()
            return None

        time.sleep(10)

        print("더 많은 호텔을 로드하기 위해 페이지를 스크롤합니다...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 10  # 최대 10번 스크롤

        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # 새로운 콘텐츠 로딩 대기

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("더 이상 로드할 콘텐츠가 없습니다.")
                break

            last_height = new_height
            scroll_count += 1
            print(f"스크롤 {scroll_count}/{max_scrolls} 완료")
            time.sleep(3)

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        print("결과 페이지 파싱을 시작합니다...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        hotel_list = []

        # 호텔 이름 요소들을 직접 찾기
        hotel_name_elements = soup.select("a[data-selenium='hotel-name']")

        if not hotel_name_elements:
            print("❌ 호텔 이름 요소를 찾지 못했습니다.")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("디버깅을 위해 'debug_page.html' 파일을 저장했습니다.")
            driver.quit()
            return None

        print(f"총 {len(hotel_name_elements)}개의 호텔 이름을 찾았습니다.")

        for i, name_element in enumerate(hotel_name_elements):
            try:
                name = name_element.text.strip()
                hotel_container = name_element
                for _ in range(10):  # 최대 10단계 상위로 이동
                    hotel_container = hotel_container.parent
                    if hotel_container is None:
                        break

                    price_element = hotel_container.select_one("[data-selenium='display-price']")
                    if price_element:
                        break

                if hotel_container is None:
                    print(f"호텔 {i+1}: 컨테이너를 찾을 수 없습니다.")
                    continue

                hotel_type = "호텔"
                location = "강남"

                score_selectors = [
                    "span.ScreenReaderOnly__ScreenReaderOnlyStyled-sc-szxtre-0",
                    "span[class*='ScreenReaderOnly']",
                    "span[class*='jifxIN']",
                    "span.ScreenReaderOnly",
                    "p[data-selenium='review-score']",
                    "span[data-selenium='review-score']",
                    ".review-score",
                    ".rating",
                    "[data-selenium*='score']"
                ]

                score = "N/A"
                for score_selector in score_selectors:
                    score_element = hotel_container.select_one(score_selector)
                    if score_element:
                        score_text = score_element.text.strip()
                        if "tooltip" in score_text.lower():
                            continue
                        if "성급" in score_text:
                            score = score_text.replace("성급", "")
                        elif any(char.isdigit() for char in score_text) and len(score_text) <= 10:
                            score = score_text
                        break

                price_selectors = [
                    "[data-selenium='display-price'] .PropertyCard__Value",
                    "[data-selenium='display-price']",
                    ".price",
                    ".hotel-price",
                    "[data-selenium*='price']"
                ]

                price = 0
                for price_selector in price_selectors:
                    price_element = hotel_container.select_one(price_selector)
                    if price_element:
                        price_text = price_element.text.strip()
                        price = ''.join(filter(str.isdigit, price_text))
                        break

                hotel_list.append({
                    "숙소명": name,
                    "숙소유형": hotel_type,
                    "위치": location,
                    "가격": int(price) if price else 0,
                    "평점": score
                })

                print(f"✅ 호텔 {i+1}: {name} - 유형: {hotel_type}, 위치: {location}, 가격: {price}, 평점: {score}")

            except Exception as e:
                print(f"호텔 {i+1} 정보를 파싱하는 중 오류 발생: {e}")
                continue

        return pd.DataFrame(hotel_list)

    except Exception as e:
        print(f"크롤링 중 오류가 발생했습니다: {e}")
        return None

    finally:
        print("크롤링을 종료합니다.")
        driver.quit()


if __name__ == "__main__":
    TARGET_DESTINATION = "강남"
    TARGET_CHECKIN = "2025-08-20"
    TARGET_CHECKOUT = "2025-08-25"
    TARGET_ADULTS = 4  # 테스트를 위해 4명으로 변경

    hotel_df = scrape_agoda_final(TARGET_DESTINATION, TARGET_CHECKIN, TARGET_CHECKOUT, TARGET_ADULTS)

    if hotel_df is not None and not hotel_df.empty:
        filename = f"agoda_{TARGET_DESTINATION}_hotels_final.csv"
        hotel_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print("\n--- 크롤링 결과 ---")
        print(hotel_df.head())
        print(f"\n✅ 성공! '{filename}' 파일로 저장되었습니다.")
    else:
        print("\n❌ 크롤링에 실패했거나 추출된 데이터가 없습니다.")
