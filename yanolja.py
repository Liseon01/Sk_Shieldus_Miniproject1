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

def crawl_yanolja(search_query):
    """
    야놀자 웹사이트에서 주어진 검색어로 숙소 정보를 크롤링하는 함수

    Args:
        search_query (str): 검색할 키워드 (예: "강남 호텔")

    Returns:
        list: 숙소 정보가 담긴 딕셔너리 리스트
    """
    # --- Selenium 웹 드라이버 설정 ---
    options = webdriver.ChromeOptions()
    
    # Cloudflare 우회를 위한 강화된 설정
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2
    })
    
    # User-Agent 설정 (실제 브라우저처럼 보이게)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # 헤드리스 모드 일시적으로 비활성화 (Cloudflare 우회를 위해)
    # options.add_argument("--headless")
    
    # 웹 드라이버 자동 설치 및 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # JavaScript 실행을 통해 webdriver 속성 숨기기
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")

    results = []

    try:
        # --- 야놀자 검색 페이지로 이동 ---
        url = f"https://nol.yanolja.com/search/{search_query}"
        print(f"접속 중: {url}")
        driver.get(url)

        # 페이지가 완전히 로드될 때까지 대기 (더 긴 시간)
        print("페이지 로딩 대기 중...")
        time.sleep(15)  # 더 오래 대기

        # Cloudflare 체크가 완료되었는지 확인
        page_source = driver.page_source
        if "일시적으로 서비스를 이용하실 수 없습니다" in page_source:
            print("Cloudflare 보안 시스템이 작동 중입니다. 더 오래 기다려보겠습니다...")
            time.sleep(20)
            driver.refresh()
            time.sleep(15)

        # --- 동적으로 로드되는 컨텐츠를 모두 가져오기 위해 스크롤 다운 ---
        print("페이지 스크롤 중...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        while scroll_count < 3:  # 최대 3번만 스크롤
            # 스크롤을 페이지 맨 아래로 내립니다.
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 새 컨텐츠가 로드될 때까지 대기
            time.sleep(3)
            
            # 새로운 스크롤 높이를 계산하고, 이전 높이와 비교합니다.
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1

        # --- 렌더링 완료된 페이지 소스를 BeautifulSoup으로 파싱 ---
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 디버깅을 위해 페이지 소스를 파일로 저장
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("페이지 소스가 debug_page.html 파일로 저장되었습니다.")

        # Cloudflare 차단 확인
        if "일시적으로 서비스를 이용하실 수 없습니다" in page_source:
            print("Cloudflare에 의해 차단되었습니다. 다른 방법을 시도해보겠습니다.")
            return []

        # 숙소 카드들을 찾기 위한 선택자
        hotel_cards = soup.find_all('a', href=lambda x: x and '/places/' in x)
        
        if not hotel_cards:
            print("숙소 카드를 찾을 수 없습니다.")
            return []

        print(f"찾은 숙소 카드 수: {len(hotel_cards)}")

        # 중복 제거를 위한 set
        seen_names = set()

        # --- 각 숙소 정보를 순회하며 데이터 추출 ---
        for i, card in enumerate(hotel_cards[:10]):  # 처음 10개만 처리 (테스트용)
            try:
                # 숙소 이름 추출 (typography-subtitle-16-bold 클래스 사용)
                name_element = card.find('p', class_='typography-subtitle-16-bold')
                name = name_element.text.strip() if name_element else 'N/A'

                # 중복 제거
                if name in seen_names or name == 'N/A':
                    continue
                seen_names.add(name)

                # 평점 추출
                rating = '평점 없음'
                rating_element = card.find('span', class_='typography-body-14-bold')
                if rating_element:
                    rating_text = rating_element.text.strip()
                    if rating_text and rating_text.replace('.', '').isdigit():
                        rating = rating_text

                # 리뷰 수 추출
                review_count = ''
                # 평점 옆의 리뷰 수를 찾기
                rating_container = card.find('p', class_='flex items-center justify-start gap-2 pl-2')
                if rating_container:
                    review_text = rating_container.get_text()
                    # 괄호 안의 숫자를 찾기
                    review_match = re.search(r'\((\d+)\)', review_text)
                    if review_match:
                        review_count = review_match.group(1)

                # 숙소 유형 추출
                hotel_type = ''
                type_element = card.find('p', class_='text-text-neutral-sub typography-body-12-regular')
                if type_element:
                    hotel_type = type_element.text.strip()

                # 위치 정보 추출
                location = ''
                location_element = card.find('span', class_='line-clamp-1 text-start')
                if location_element:
                    location = location_element.text.strip()

                # 검색 결과 페이지에서 가격 정보 추출 (개선된 방법)
                price = '가격 정보 없음'
                
                # 정확한 가격 정보만 추출하기 위한 정규식 패턴
                price_patterns = [
                    r'(\d{1,3}(?:,\d{3})*원)',
                    r'(\d+원)',
                    r'(\d{1,3}(?:,\d{3})*원~)',
                    r'(\d+원~)'
                ]
                
                # 카드의 모든 텍스트에서 가격 찾기
                card_text = card.get_text()
                for pattern in price_patterns:
                    price_matches = re.findall(pattern, card_text)
                    if price_matches:
                        # 가장 짧은 가격 정보 선택 (가장 정확한 것)
                        price = min(price_matches, key=len)
                        break
                
                # 위 방법으로 찾지 못한 경우 다른 방법 시도
                if price == '가격 정보 없음':
                    # 다양한 가격 선택자 시도
                    price_selectors = [
                        'span[class*="price"]',
                        'span[class*="cost"]',
                        'span[class*="amount"]',
                        'div[class*="price"]',
                        'div[class*="cost"]',
                        'div[class*="amount"]',
                        'span[class*="typography-subtitle-16-bold"]',
                        'span[class*="typography-subtitle-18-bold"]'
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elements = card.select(selector)
                            for price_element in price_elements:
                                price_text = price_element.text.strip()
                                if price_text and '원' in price_text and re.search(r'\d+원', price_text):
                                    # 정규식으로 정확한 가격만 추출
                                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*원)', price_text)
                                    if price_match:
                                        price = price_match.group(1)
                                        break
                            if price != '가격 정보 없음':
                                break
                        except:
                            continue

                results.append({
                    '숙소명': name,
                    '숙소유형': hotel_type,
                    '위치': location,
                    '평점': f"{rating} ({review_count})" if review_count else rating,
                    '가격': price
                })

            except Exception as e:
                print(f"개별 숙소 정보 추출 중 오류: {e}")
                continue

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    finally:
        # 웹 드라이버 종료
        driver.quit()

    return results

# --- 메인 코드 실행 ---
if __name__ == "__main__":
    # 검색어를 여기에 입력하세요.
    query = "고양시"
    
    print(f"'{query}'에 대한 검색 결과를 크롤링합니다...")
    
    scraped_data = crawl_yanolja(query)

    if scraped_data:
        # 보기 좋게 출력하기 위해 pandas DataFrame 사용 (선택 사항)
        df = pd.DataFrame(scraped_data)
        print(f"\n총 {len(df)}개의 숙소 정보를 찾았습니다.")
        print("\n" + "="*80)
        print(df)
        print("="*80)
        
        # CSV 파일로 저장
        filename = f"{query.replace(' ', '_')}_yanolja.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n'{filename}' 파일로 저장이 완료되었습니다.")
    else:
        print("크롤링된 데이터가 없습니다.")