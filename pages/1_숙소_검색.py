import streamlit as st
st.set_page_config(page_title="숙소 가격 비교 대시보드", layout="wide")

import pandas as pd
from modules.scraping_modules.yanolja import crawl_yanolja
from modules.scraping_modules.yeogi import crawl_yeogi_to_csv
from modules.scraping_modules.trivago import crawl_trivago_final
from modules.rank_modules.rank_all import crawl_all_sources
import os
import plotly.express as px

# ✅ 사이드바: 검색 조건 입력
# 사이드바 입력: 검색 조건
with st.sidebar:
    st.header("🔍 검색 조건")
    destination = st.text_input("여행지", value="서울")
    checkin = st.date_input("체크인 날짜")
    checkout = st.date_input("체크아웃 날짜")
    adults = st.number_input("성인 인원 수", min_value=1, max_value=10, value=2)

    # 검색 버튼만 존재
    if st.button("🔎 숙소 검색"):
        result_df = run_all_crawlers(destination, checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), adults)
        st.session_state["result_df"] = result_df
        st.rerun()  

# 데이터가 저장된 경우만 아래 필터 UI, 출력 표시
if "result_df" in st.session_state and not st.session_state["result_df"].empty:
    df = st.session_state["result_df"].copy()

    # 사이드바 가격 필터 슬라이더
    with st.sidebar:
        st.markdown("---")
        st.header("💸 가격 필터")
        valid_prices = df["가격(원)"].dropna().astype(int)
        min_price = int(valid_prices.min())
        max_price = int(valid_prices.max())
        price_min, price_max = st.slider(
            "1박당 요금 (원)",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            step=10000
        )

    # 👉 가격 필터 적용
    df = df.dropna(subset=["가격(원)"])
    df = df[df["가격(원)"].between(price_min, price_max)]

    # 정렬 옵션
    sort_option = st.selectbox("정렬 기준을 선택하세요", ["가격(낮은순)", "평점(높은순)", "가성비(높은순)"])
    if sort_option == "가격(낮은순)":
        df = df.sort_values("가격(원)")
    elif sort_option == "평점(높은순)":
        df = df.sort_values("평점", ascending=False)
    elif sort_option == "가성비(높은순)":
        df = df.sort_values("가성비", ascending=False)

    def make_hyperlink(name, url):
        if pd.notna(url) and url != "None":
            return f'<a href="{url}" target="_blank">{name}</a>'
        return name

    df['숙소명'] = df.apply(lambda row: make_hyperlink(row['숙소명'], row['링크']), axis=1)
    display_df = df[['숙소명', '숙소유형', '위치', '가격', '평점', '가성비', '출처']].copy()

    scrollable_table = f"""
    <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 5px;">
        {display_df.to_html(escape=False, index=False)}
    </div>
    """
    st.markdown(scrollable_table, unsafe_allow_html=True)

    # 📊 숙소유형별 평균 가격
    st.subheader("🏨 숙소유형별 평균 가격")
    type_avg = df.dropna(subset=["가격(원)"]).groupby("숙소유형")["가격(원)"].mean().reset_index()
    fig1 = px.pie(type_avg, names="숙소유형", values="가격(원)", title="숙소유형별 평균 가격", hole=0.4)
    st.plotly_chart(fig1, use_container_width=True)

    # 📊 출처별 숙소 수
    st.subheader("📦 출처별 숙소 수")
    src_count = df["출처"].value_counts().reset_index()
    src_count.columns = ["출처", "숙소 수"]
    fig2 = px.pie(src_count, names="출처", values="숙소 수", title="출처별 숙소 분포", hole=0.5)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("좌측에서 검색 후 결과가 여기에 표시됩니다.")
