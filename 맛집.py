import requests
import re
from collections import defaultdict

CLIENT_ID = "zJ9cQ9L23e3ORhQEBskW"
CLIENT_SECRET = "9vPrljlqX0"

def search_local_place(place_name, display=1):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {
        "query": place_name,
        "display": display,
        "sort": "sim"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("장소 검색 API 요청 실패:", response.status_code, response.text)
        return []
    data = response.json()
    return data.get("items", [])

def search_restaurants(place_name, category, display=10):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    query = f"{place_name} {category} 맛집"
    params = {
        "query": query,
        "display": display,
        "sort": "sim"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("맛집 API 요청 실패:", response.status_code, response.text)
        return []
    data = response.json()
    return data.get("items", [])

def get_area_from_address(address):
    # 주소에서 ‘구’ ‘군’ ‘시’ 추출 예시
    for part in address.split():
        if part.endswith(("구", "군", "시")):
            return part
    parts = address.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    elif parts:
        return parts[0]
    return ""

def clean_html(text):
    return re.sub('<.*?>', '', text)

def search_festivals(area, display=30):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    query = f"{area} 2025년 축제"
    params = {
        "query": query,
        "display": display,
        "sort": "sim"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("축제 검색 API 요청 실패:", response.status_code, response.text)
        return []
    data = response.json()
    return data.get("items", [])

def extract_date_info(text):
    patterns = [
        r'2025년\s*\d{1,2}월\s*\d{1,2}일',
        r'2025년\s*\d{1,2}월',
        r'\d{1,2}월\s*\d{1,2}일',
        r'\d{1,2}월',
    ]
    matches = []
    for p in patterns:
        found = re.findall(p, text)
        if found:
            matches.extend(found)
    return list(set(matches))

def main():
    place = input("숙소명 입력: ")

    # 1) 숙소명으로 위치 정보 가져오기
    place_results = search_local_place(place, display=1)
    if not place_results:
        print("숙소 위치 정보를 찾을 수 없습니다.")
        return
    address = place_results[0].get("roadAddress") or place_results[0].get("address") or ""
    area = get_area_from_address(address)
    print(f"\n입력 숙소 주소: {address}")
    print(f"추출된 지역명: {area}")

    # 2) 맛집 검색
    categories = ["한식", "중식", "일식", "양식"]
    for cat in categories:
        print(f"\n[{cat} 맛집]")
        results = search_restaurants(place, cat)
        if not results:
            print("검색 결과가 없습니다.")
            continue
        for i, item in enumerate(results, 1):
            name = clean_html(item["title"])
            addr = item.get("roadAddress") or item.get("address") or "주소 없음"
            print(f"{i}. {name} - {addr}")

    # 3) 지역명 포함 축제 검색 및 날짜별 그룹핑
    print(f"\n[{area} 지역 2025년 축제 관련 블로그 검색 결과 - 날짜별 정리]")
    festival_results = search_festivals(area)

    if not festival_results:
        print("검색 결과가 없습니다.")
        return

    from collections import defaultdict
    festivals_by_date = defaultdict(list)

    for item in festival_results:
        title = clean_html(item['title'])
        link = item['link']
        description = clean_html(item.get('description', ''))
        dates = extract_date_info(description)
        if not dates:
            festivals_by_date['날짜 미상'].append((title, link, description))
        else:
            for d in dates:
                festivals_by_date[d].append((title, link, description))

    for date in sorted(festivals_by_date.keys()):
        print(f"\n=== {date} ===")
        for i, (title, link, description) in enumerate(festivals_by_date[date], 1):
            print(f"{i}. {title}")
            print(f"   링크: {link}")
            print(f"   설명: {description}")

if __name__ == "__main__":
    main()
