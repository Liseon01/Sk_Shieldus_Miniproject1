import streamlit as st
import requests
import re
from collections import defaultdict

st.set_page_config(page_title="맛집 & 검색 탐색기", layout="wide")

# --- CSS 적용 코드 시작 ---
def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")
# --- CSS 적용 코드 끝 ---


# Naver API 키
CLIENT_ID = "zJ9cQ9L23e3ORhQEBskW"
CLIENT_SECRET = "9vPrljlqX0"

# 지역 정보 추출
def get_area_from_address(address):
    for part in address.split():
        if part.endswith(("구", "군", "시")):
            return part
    parts = address.split()
    return f"{parts[0]} {parts[1]}" if len(parts) >= 2 else (parts[0] if parts else "")

# 맛집 검색
def search_restaurants(area, category_list=["한식", "중식", "일식", "양식"]):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    results_by_category = {}
    for cat in category_list:
        query = f"{area} {cat} 맛집"
        params = {"query": query, "display": 5, "sort": "sim"}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            results_by_category[cat] = []
            continue
        data = r.json()
        results_by_category[cat] = data.get("items", [])
    return results_by_category

# 축제 검색
def search_festivals(area):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": f"{area} 2025년 축제", "display": 30, "sort": "sim"}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return {}
    items = r.json().get("items", [])
    return group_festivals_by_date(items)

# HTML 태그 제거
def clean_html(text):
    return re.sub('<.*?>', '', text)

# 날짜 정보 추출
def extract_date_info(text):
    patterns = [r'2025년\s*\d{1,2}월\s*\d{1,2}일', r'2025년\s*\d{1,2}월', r'\d{1,2}월\s*\d{1,2}일', r'\d{1,2}월']
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, text))
    return list(set(matches))

# 축제를 날짜별로 묶기
def group_festivals_by_date(items):
    festivals_by_date = defaultdict(list)
    for item in items:
        title = clean_html(item["title"])
        link = item["link"]
        desc = clean_html(item.get("description", ""))
        dates = extract_date_info(desc)
        if not dates:
            festivals_by_date["날짜 미상"].append((title, link, desc))
        else:
            for d in dates:
                festivals_by_date[d].append((title, link, desc))
    return festivals_by_date

# 📍 UI
st.title("📍 맛집 & 축제 검색기")

with st.form("search_form"):
    address = st.text_input("현재 주소를 입력하세요 (예: 서울특별시 광진구 화양동)")
    submitted = st.form_submit_button("검색하기")

if submitted and address:
    area = get_area_from_address(address)
    st.subheader(f"🔍 '{area}' 지역 검색 결과")

    tabs = st.tabs(["🍽️ 맛집 추천", "🎉 2025 축제 정보"])

    # ▶ 맛집 탭
    with tabs[0]:
        restaurant_data = search_restaurants(area)
        st.markdown("### ✅ 카테고리별 Top 5 맛집")

        col1, col2 = st.columns(2)
        category_keys = list(restaurant_data.keys())
        half = (len(category_keys) + 1) // 2

        for idx, cat in enumerate(category_keys):
            target_col = col1 if idx < half else col2
            with target_col:
                st.markdown(f"#### 📌 {cat}")
                if not restaurant_data[cat]:
                    st.write("검색 결과가 없습니다.")
                else:
                    for i in restaurant_data[cat]:
                        name = clean_html(i['title'])
                        link = i['link']
                        st.markdown(f"- [{name}]({link})")

    # ▶ 축제 탭
    with tabs[1]:
        festival_data = search_festivals(area)
        st.markdown("### 🎊 날짜별 축제 모음")

        if not festival_data:
            st.info("축제 정보를 불러올 수 없습니다.")
        else:
            for date in sorted(festival_data.keys()):
                st.markdown(f"#### 📅 {date}")
                cols = st.columns(2)
                entries = festival_data[date]
                for idx, (title, link, desc) in enumerate(entries):
                    with cols[idx % 2]:
                        st.markdown(
                            f"""
                            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:8px;">
                                <b><a href="{link}" target="_blank">{title}</a></b><br/>
                                <small>{desc}</small>
                            </div>
                            """, unsafe_allow_html=True
                        )