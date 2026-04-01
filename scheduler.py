"""
스케줄러: 매일 오전 9시 자동 크롤링 + 결과 비교 알림
실행: python scheduler.py
"""

import schedule
import time
import json
import os
from datetime import datetime
from crawler import run_all, save_results

OUTPUT_DIR  = "output"
PREV_FILE   = os.path.join(OUTPUT_DIR, "previous_run.json")


def load_previous() -> set:
    """이전 실행 결과의 타이틀 집합 로드"""
    if not os.path.exists(PREV_FILE):
        return set()
    with open(PREV_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(item.get("title", "") for item in data)


def save_previous(results: list[dict]):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(PREV_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def detect_new_items(results: list[dict], previous_titles: set) -> list[dict]:
    """이전 결과에 없는 신규 항목만 필터"""
    return [r for r in results if r.get("title", "") not in previous_titles]


def job():
    print(f"\n{'='*50}")
    print(f"자동 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    previous_titles = load_previous()
    results = run_all()
    save_results(results)

    new_items = detect_new_items(results, previous_titles)
    new_bm    = [i for i in new_items if i.get("type") == "BM/캐시샵"]

    if new_bm:
        print(f"\n🚨 신규 BM 감지: {len(new_bm)}건")
        for item in new_bm:
            print(f"  [{item['game']}] {item['title']}")
            print(f"   → {item.get('link', '')}")
    elif new_items:
        print(f"\n📌 신규 공지 {len(new_items)}건 (BM 외)")
    else:
        print("\n✅ 신규 항목 없음")

    save_previous(results)


if __name__ == "__main__":
    print("스케줄러 시작 — 매일 오전 9시 자동 실행")
    print("지금 바로 한 번 실행합니다...\n")
    job()

    schedule.every().day.at("09:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)
