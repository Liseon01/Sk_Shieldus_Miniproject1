import requests

CLIENT_ID = "zJ9cQ9L23e3ORhQEBskW"
CLIENT_SECRET = "9vPrljlqX0"

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
        "sort": "random"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("API 요청 실패:", response.status_code, response.text)
        return []
    data = response.json()
    return data.get("items", [])

def clean_html(text):
    return text.replace("<b>", "").replace("</b>", "")

def main():
    place = input("숙소명 입력: ")
    categories = ["한식", "중식", "일식", "양식"]
    
    for cat in categories:
        print(f"\n[{cat} 맛집]")
        results = search_restaurants(place, cat)
        if not results:
            print("검색 결과가 없습니다.")
            continue
        for i, item in enumerate(results, 1):
            name = clean_html(item["title"])
            address = item.get("address", "주소 없음")
            print(f"{i}. {name} - {address}")

if __name__ == "__main__":
    main()
