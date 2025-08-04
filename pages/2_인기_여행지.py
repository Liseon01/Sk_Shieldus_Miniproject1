import streamlit as st
st.set_page_config(page_title="숙소 가격 비교 대시보드", layout="wide")

import pandas as pd
from modules.scraping_modules.yanolja import crawl_yanolja
from modules.scraping_modules.yeogi import crawl_yeogi_to_csv
from modules.scraping_modules.trivago import crawl_trivago_final
from modules.rank_modules.rank_all import crawl_all_sources
import os
import plotly.express as px

# ───────────────────────────────────────────────
# ▶ 인기 여행지 미리 불러오기 (캐시로 속도 개선)
# ───────────────────────────────────────────────
@st.cache_data(show_spinner="인기 여행지 가져오는 중...")
def get_popular_destinations():
    return crawl_all_sources()

popular_destinations = get_popular_destinations()

# ───────────────────────────────────────────────
# ▶ 데이터 크롤링 및 통합 함수
# ───────────────────────────────────────────────
def run_all_crawlers(destination, checkin, checkout, adults):
    st.info(f"입력 정보 - 지역: {destination}, 체크인: {checkin}, 체크아웃: {checkout}, 성인: {adults}명")

    with st.spinner('야놀자 크롤링 중...'):
        df_yanolja = crawl_yanolja(destination, checkin, checkout, adults, children=0, save_csv=False)
        df_yanolja['출처'] = '야놀자'
        if '링크' not in df_yanolja.columns:
            df_yanolja['링크'] = None

    with st.spinner('여기어때 크롤링 중...'):
        yeogi_csv = crawl_yeogi_to_csv(destination, checkin, checkout, adults)
        df_yeogi = pd.read_csv(yeogi_csv)
        df_yeogi['출처'] = '여기어때'
        os.remove(yeogi_csv)
        if '링크' not in df_yeogi.columns:
            df_yeogi['링크'] = None

    with st.spinner('트리바고 크롤링 중...'):
        trivago_data = crawl_trivago_final(destination, checkin, checkout, adults)
        df_trivago = pd.DataFrame(trivago_data)
        df_trivago['출처'] = '트리바고'
        df_trivago['링크'] = None

    all_df = pd.concat([df_yanolja, df_yeogi, df_trivago], ignore_index=True)
    all_df = all_df[['숙소명', '숙소유형', '위치', '평점', '가격', '출처', '링크']]

    def extract_price(value):
        if isinstance(value, str):
            digits = ''.join(filter(str.isdigit, value))
            return int(digits) if digits else None
        return None

    all_df['가격(원)'] = all_df['가격'].apply(extract_price)
    all_df['평점'] = pd.to_numeric(all_df['평점'], errors='coerce')
    all_df['가성비'] = all_df.apply(
        lambda row: (row['평점'] / row['가격(원)']) if row['가격(원)'] and row['평점'] else None,
        axis=1
    )

    return all_df

# ───────────────────────────────────────────────
# ▶ Streamlit UI
# ───────────────────────────────────────────────
st.title("🛏️ 숙소 가격/평점/가성비 비교 대시보드")

# ✅ 인기 여행지 카드형 UI (3열 병렬)
st.subheader("📋 플랫폼별 인기 여행지 Top 5")
platforms = list(popular_destinations.keys())
columns = st.columns(len(platforms))

for idx, platform in enumerate(platforms):
    with columns[idx]:
        st.markdown(f"### 🏷️ {platform}")
        for place in popular_destinations[platform][:5]:
            st.markdown(
                f"""
                <div style="
                    background-color: #f9f9f9;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
                ">
                    <span style="font-size: 16px;">📍 <b>{place}</b></span>
                </div>
                """,
                unsafe_allow_html=True
            )
