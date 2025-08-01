# rank_all.py

from rank_trivago import get_trivago_destinations
from rank_yanolja import get_yanolja_popular_destinations_selenium
from rank_yeogi import get_yeogi_keywords
from rank_agoda import scrape_korean_destinations_headless

import pandas as pd


def crawl_all_sources():
    """
    모든 사이트의 인기 여행지를 크롤링하여 딕셔너리로 반환.
    """
    results = {}

    try:
        print("🚀 Trivago 크롤링 중...")
        results["Trivago"] = get_trivago_destinations()
    except Exception as e:
        print(f"❌ Trivago 오류: {e}")
        results["Trivago"] = []

    try:
        print("🚀 야놀자 크롤링 중...")
        results["Yanolja"] = get_yanolja_popular_destinations_selenium()
    except Exception as e:
        print(f"❌ Yanolja 오류: {e}")
        results["Yanolja"] = []

    try:
        print("🚀 여기어때 크롤링 중...")
        results["Yeogi"] = get_yeogi_keywords()
    except Exception as e:
        print(f"❌ Yeogi 오류: {e}")
        results["Yeogi"] = []

    try:
        print("🚀 Agoda 크롤링 중...")
        results["Agoda"] = scrape_korean_destinations_headless()
    except Exception as e:
        print(f"❌ Agoda 오류: {e}")
        results["Agoda"] = []

    return results


def print_results(results):
    """
    크롤링 결과를 콘솔에 출력.
    """
    for source, items in results.items():
        print(f"\n📌 [{source}] 인기 여행지 목록")
        if not items:
            print("  (데이터 없음)")
            continue
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")


def save_to_csv(results, filename="rank_all_combined.csv"):
    """
    크롤링 결과를 CSV 파일로 저장.
    """
    rows = []
    for source, items in results.items():
        for rank, region in enumerate(items, 1):
            rows.append([source, rank, region])

    df = pd.DataFrame(rows, columns=["Source", "Rank", "Region"])
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n💾 저장 완료: {filename}")


if __name__ == "__main__":
    all_results = crawl_all_sources()
    print_results(all_results)
    save_to_csv(all_results)
