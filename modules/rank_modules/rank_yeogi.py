import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def get_yeogi_keywords():
    """
    여기어때 인기 검색 키워드를 크롤링하여 리스트로 반환.
    """
    # 크롬 옵션 설정 (헤드리스 모드)
    options = Options()
    options.add_argument("--headless=new")  
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 드라이버 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    keywords = []

    try:
        driver.get("https://www.yeogi.com/")
        time.sleep(3)

        # 인기 검색 키워드 섹션 범위 지정
        popular_section = driver.find_element(By.CSS_SELECTOR, 'section[aria-label="인기 검색 키워드"]')

        # 해당 섹션 내부에서만 검색어 추출
        keyword_elements = popular_section.find_elements(
            By.CSS_SELECTOR,
            'div.css-grswmc > a'
        )

        keywords = [el.text.strip() for el in keyword_elements if el.text.strip()]

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

    return keywords

if __name__ == "__main__":
    results = get_yeogi_keywords()
    print("📌 여기어때 인기 검색어:")
    for i, keyword in enumerate(results, start=1):
        print(f"{i}위: {keyword}")
