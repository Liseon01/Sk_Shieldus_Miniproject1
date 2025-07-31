from datetime import datetime, timedelta
from yeogi import crawl_yeogi_to_csv  # 네 코드 파일명이 yeogi.py라고 가정

def main():
    # 테스트용 기본 파라미터 설정
    destination = "강릉"
    
    today = datetime.today()
    checkin = (today + timedelta(days=7)).strftime("%Y-%m-%d")   # 오늘 기준 7일 뒤 체크인
    checkout = (today + timedelta(days=8)).strftime("%Y-%m-%d")  # 1박 후 체크아웃
    adults = 2

    print(f"[TEST] 여기어때 크롤링 시작: {destination}, {checkin} ~ {checkout}, 성인 {adults}명")
    csv_filename = crawl_yeogi_to_csv(destination, checkin, checkout, adults)

    print(f"[TEST 완료] 저장된 파일: {csv_filename}")

if __name__ == "__main__":
    main()
