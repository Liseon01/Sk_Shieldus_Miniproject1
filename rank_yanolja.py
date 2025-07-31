import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_yanolja_popular_destinations_selenium():
    """
    Selenium을 사용하여 동적으로 로드되는 야놀자 인기 여행지를 크롤링합니다.
    """
    # 1. 크롤링할 목표 URL
    url = "https://nol.yanolja.com/search"
    
    # 2. Selenium 웹드라이버 설정
    # ChromeDriverManager가 크롬 버전에 맞는 드라이버를 자동으로 설치해줍니다.
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # 브라우저 창을 띄우지 않고 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like; Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    destinations = []
    try:
        # 3. 웹사이트 열기
        driver.get(url)
        
        # 4. 자바스크립트가 데이터를 로드할 시간을 줌 (3초 대기)
        time.sleep(3)
        
        # 5. 완전히 로딩된 페이지의 HTML 소스 가져오기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 6. 제공해주신 단서에 있는 정확한 클래스 이름으로 검색
        popular_items = soup.find_all('span', class_='PopularSearchList_keyword__1LfLt')
        
        # 7. 텍스트만 추출하여 리스트에 저장
        destinations = [item.get_text() for item in popular_items]
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    finally:
        # 8. 작업이 끝나면 브라우저 닫기
        driver.quit()
        
    return destinations

# --- 코드 실행 ---
if __name__ == "__main__":
    popular_list = get_yanolja_popular_destinations_selenium()

    if popular_list:
        print("✈️ 야놀자 현재 인기 여행지 TOP 10 (성공!)")
        print("---------------------------------------")
        for rank, destination in enumerate(popular_list, 1):
            print(f"{rank}위: {destination}")
    else:
        print("인기 여행지를 가져오는 데 실패했습니다.")