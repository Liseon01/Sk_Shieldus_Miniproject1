import streamlit as st
import pandas as pd
from yanolja import crawl_yanolja
from yeogi import crawl_yeogi_to_csv
from trivago import crawl_trivago_final
import os
import plotly.express as px

# ───────────────────────────────────────────────
# ▶ 데이터 크롤링 및 통합 함수
# ───────────────────────────────────────────────
def run_all_crawlers(destination, checkin, checkout, adults):
    st.info(f"입력 정보 - 지역: {destination}, 체크인: {checkin}, 체크아웃: {checkout}, 성인: {adults}명")

    # 1. 야놀자
    with st.spinner('야놀자 크롤링 중...'):
        df_yanolja = crawl_yanolja(destination, checkin, checkout, adults, children=0, save_csv=False)
        df_yanolja['출처'] = '야놀자'

    # 2. 여기어때
    with st.spinner('여기어때 크롤링 중...'):
        yeogi_csv = crawl_yeogi_to_csv(destination, checkin, checkout, adults)
        df_yeogi = pd.read_csv(yeogi_csv)
        df_yeogi['출처'] = '여기어때'
        os.remove(yeogi_csv)

    # 3. 트리바고
    with st.spinner('트리바고 크롤링 중...'):
        trivago_data = crawl_trivago_final(destination, checkin, checkout, adults, max_results=30)
        df_trivago = pd.DataFrame(trivago_data)
        df_trivago['출처'] = '트리바고'

    # 열 통일
    all_df = pd.concat([df_yanolja, df_yeogi, df_trivago], ignore_index=True)
    all_df = all_df[['숙소명', '숙소유형', '위치', '평점', '가격', '출처']]

    # 가격 숫자 추출
    def extract_price(value):
        if isinstance(value, str):
            digits = ''.join(filter(str.isdigit, value))
            return int(digits) if digits else None
        return None

    all_df['가격(원)'] = all_df['가격'].apply(extract_price)
    all_df['평점'] = pd.to_numeric(all_df['평점'], errors='coerce')

    # 가성비 계산: 평점 / 가격
    all_df['가성비'] = all_df.apply(lambda row: (row['평점'] / row['가격(원)']) if row['가격(원)'] and row['평점'] else None, axis=1)

    return all_df

# ───────────────────────────────────────────────
# ▶ Streamlit UI 시작
# ───────────────────────────────────────────────
st.set_page_config(page_title="숙소 가격 비교 대시보드", layout="wide")
st.title("🛏️ 숙소 가격/평점/가성비 비교 대시보드")

with st.sidebar:
    st.header("🔍 검색 조건")
    destination = st.text_input("여행지", value="서울")
    checkin = st.date_input("체크인 날짜")
    checkout = st.date_input("체크아웃 날짜")
    adults = st.number_input("성인 인원 수", min_value=1, max_value=10, value=2)
    search_btn = st.button("🔎 검색 및 크롤링 실행")

if search_btn:
    result_df = run_all_crawlers(destination, checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), adults)
    st.session_state["result_df"] = result_df
    st.success(f"총 {len(result_df)}개 숙소 정보를 수집했습니다.")

sort_option = st.selectbox("정렬 기준을 선택하세요", ["가격(낮은순)", "평점(높은순)", "가성비(높은순)"])

if "result_df" in st.session_state:
    df = st.session_state["result_df"].copy()

    if sort_option == "가격(낮은순)":
        df = df.sort_values("가격(원)", ascending=True)
    elif sort_option == "평점(높은순)":
        df = df.sort_values("평점", ascending=False)
    elif sort_option == "가성비(높은순)":
        df = df.sort_values("가성비", ascending=False)

    st.dataframe(df[['숙소명', '숙소유형', '위치', '가격', '평점', '가성비', '출처']])


    # ─────────────────────────────
    # 📈 신규 시각화 (1) 숙소유형별 평균 가격
    # ─────────────────────────────
    st.subheader("🏨 숙소유형별 평균 가격")
    type_avg = df.dropna(subset=["가격(원)"]).groupby("숙소유형")["가격(원)"].mean().reset_index()
    fig1 = px.pie(type_avg, names="숙소유형", values="가격(원)", title="숙소유형별 평균 가격", hole=0.4)
    st.plotly_chart(fig1, use_container_width=True)

    # ─────────────────────────────
    # 📊 신규 시각화 (2) 출처별 숙소 수
    # ─────────────────────────────
    st.subheader("📦 출처별 숙소 수")
    src_count = df["출처"].value_counts().reset_index()
    src_count.columns = ["출처", "숙소 수"]
    fig2 = px.pie(src_count, names="출처", values="숙소 수", title="출처별 숙소 분포", hole=0.5)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("좌측에서 검색 후 결과가 여기에 표시됩니다.")
