import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

def crawl_yeogi_to_csv(destination: str, checkin: str, checkout: str, adults: int) -> str:
    keyword = destination.replace(" ", "+")
    filename = destination.replace(" ", "_") + "_yeogi.csv"

    page = 1
    results = []

    options = Options()
    options.add_argument("--window-size=1200,800")
    options.add_argument("--headless=new")  # UI 없이 실행 (선택사항)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    while True:
        url = f"https://www.yeogi.com/domestic-accommodations?keyword={keyword}&checkIn={checkin}&checkOut={checkout}&personal={adults}&freeForm=false&page={page}"
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name_tags = soup.select("h3.gc-thumbnail-type-seller-card-title")
        type_tags = soup.select("ul.css-bl7zf6 li:first-child")
        location_blocks = soup.select("div.css-19li9i9")
        rating_tags = soup.select("div.css-19f645y span.css-9ml4lz")
        price_tags = soup.select("div.css-yeouz0")

        n = min(len(name_tags), len(type_tags), len(location_blocks), len(rating_tags), len(price_tags))

        if n == 0:
            print(f"[INFO] Page {page}: 숙소 없음, 종료.")
            break

        print(f"[INFO] Page {page}: 숙소 {n}개 크롤링 중...")

        for i in range(n):
            name = name_tags[i].text.strip()
            acc_type = type_tags[i].text.strip()
            location = " ".join([span.text.strip() for span in location_blocks[i].select("span")])
            rating = rating_tags[i].text.strip()
            price_tag = price_tags[i]

            if price_tag:
                price_parts = [span.get_text(strip=True) for span in price_tag.select("span")]
                price_text = " ".join(price_parts).replace(" 원", "원").replace(" /", "/")
            else:
                price_text = "없음"

            results.append([name, acc_type, location, rating, price_text])

        page += 1

    driver.quit()

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["이름", "유형", "위치", "평점", "가격"])
        writer.writerows(results)

    print(f"[완료] CSV 저장: {filename}")
    return filename