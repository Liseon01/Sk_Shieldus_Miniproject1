import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_yanolja_popular_destinations_selenium():
    """
    야놀자 인기 여행지를 크롤링하여 리스트로 반환.
    """
    url = "https://nol.yanolja.com/search"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like; Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    destinations = []

    try:
        driver.get(url)
        time.sleep(3)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        popular_items = soup.find_all('span', class_='PopularSearchList_keyword__1LfLt')
        destinations = [item.get_text(strip=True) for item in popular_items if item.get_text(strip=True)]

    except Exception as e:
        print(f"❌ 야놀자 스크래핑 오류: {e}")
    finally:
        driver.quit()

    return destinations

if __name__ == "__main__":
    popular_list = get_yanolja_popular_destinations_selenium()
    print("📍 야놀자 인기 여행지:")
    for i, destination in enumerate(popular_list, 1):
        print(f"{i}위: {destination}")
