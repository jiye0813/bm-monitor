"""
경쟁사 외형 BM 모니터링 크롤러 v4
- 메이플스토리: 캐시샵 공지만 (외형 관련 키워드 필터링)
- 로스트아크: 상점 말머리 + 30일 이내
- 파이널판타지14: 네이버 파판 샵 크롤링
- 아이온2: 공지 전체
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import re
from datetime import datetime, timedelta
from time import sleep

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 메이플 캐시샵 외형 관련 키워드 (이것 포함된 공지만 수집)
MAPLE_COSTUME_KEYWORDS = [
    "코디", "헤어", "성형", "스타일", "의상", "코스튬", "외형",
    "로얄", "마스터피스", "패션", "스킨", "뷰티", "룩북",
]

BM_KEYWORDS     = ["캐시", "크샵", "상점", "판매", "패키지", "코스튬", "의상", "외형", "스킨", "뽑기", "확률", "로얄", "헤어", "성형", "쿠폰", "코디"]
EVENT_KEYWORDS  = ["이벤트", "프로모션", "할인", "혜택", "보상", "증정", "선물", "기념"]
UPDATE_KEYWORDS = ["업데이트", "패치", "점검", "신규", "추가", "변경"]

def classify(title, badge=""):
    text = (title + badge).lower()
    if any(k in text for k in BM_KEYWORDS):     return "BM/캐시샵"
    if any(k in text for k in EVENT_KEYWORDS):  return "이벤트"
    if any(k in text for k in UPDATE_KEYWORDS): return "업데이트"
    return "공지"

def url_sort_key(item: dict) -> int:
    nums = re.findall(r"\d+", item.get("link", ""))
    return int(nums[-1]) if nums else 0

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_page(driver, url, wait_selector="body", timeout=10):
    driver.get(url)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
    except Exception:
        pass
    sleep(2)
    return BeautifulSoup(driver.page_source, "html.parser")

def dedup_by_link(results: list) -> list:
    seen, out = set(), []
    for d in results:
        key = d.get("link", d.get("title", ""))
        if key and key not in seen:
            seen.add(key)
            out.append(d)
    return sorted(out, key=url_sort_key, reverse=True)


# ─────────────────────────────────────────────
# 1. 메이플스토리 캐시샵 — 외형 관련만
# ─────────────────────────────────────────────

def crawl_maple_cashshop(driver):
    """
    /News/CashShop/Sale/숫자 패턴 링크만 수집
    제목에 외형 키워드 포함된 것만 필터링
    """
    url = "https://maplestory.nexon.com/News/CashShop"
    results = []
    try:
        soup = fetch_page(driver, url, "body", timeout=10)
        links = soup.select("a[href*='/CashShop/Sale/']")
        for a in links:
            href  = a.get("href", "")
            # 제목: a 태그 내 텍스트에서 수정/날짜 등 제거
            raw   = a.get_text(separator=" ", strip=True)
            # "수정" 태그 텍스트 제거
            title = re.sub(r"^\s*(수정\d*|NEW)\s*", "", raw).strip()
            # 날짜 패턴 추출 (예: "2026.03.23 ~ 2026.06.17" 또는 "상시판매")
            date_match = re.search(r"(\d{4}\.\d{2}\.\d{2}.*)", raw)
            period = date_match.group(1) if date_match else ""

            if not href.startswith("http"):
                href = "https://maplestory.nexon.com" + href

            # 외형 키워드 포함 여부 확인
            if not any(k in title for k in MAPLE_COSTUME_KEYWORDS):
                continue

            if title:
                results.append({
                    "game": "메이플스토리",
                    "type": "BM/캐시샵",
                    "title": title,
                    "date": period,
                    "link": href,
                })
    except Exception as e:
        print(f"  오류: {e}")
    return dedup_by_link(results)


# ─────────────────────────────────────────────
# 2. 로스트아크 — 상점 말머리 + 30일 이내
# ─────────────────────────────────────────────

def parse_lostark_date(title: str) -> datetime | None:
    """
    제목에서 날짜 파싱
    예: "4월 1일(수) 신규 상품 및 확률 안내" → datetime(2026, 4, 1)
    """
    today = datetime.now()
    # "M월 D일" 패턴
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", title)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = today.year
        # 12월 공지인데 현재가 1~2월이면 작년
        if month > today.month + 2:
            year -= 1
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    return None

def crawl_lostark(driver):
    """
    상점 말머리 글만 수집 + 30일 이내 필터링
    a 태그 텍스트를 줄 단위로 분리:
      줄1 = 말머리 ("상점")
      줄2 = 제목
      줄N = 날짜
    """
    url = "https://lostark.game.onstove.com/News/Notice/List?noticetype=shop"
    results = []
    cutoff = datetime.now() - timedelta(days=30)
    try:
        soup = fetch_page(driver, url, "body", timeout=10)
        links = soup.select("a[href*='/News/Notice/Views/']")
        for a in links:
            lines = [l.strip() for l in a.get_text(separator="\n").split("\n") if l.strip()]
            if not lines or lines[0] != "상점":
                continue

            title = lines[1] if len(lines) > 1 else ""
            date  = lines[-1] if len(lines) > 2 else ""
            # "새 글", "9999+" 같은 노이즈 날짜 정리
            if not re.search(r"\d{4}\.\d{2}\.\d{2}|시간 전|분 전|일 전", date):
                date = ""

            href = a.get("href", "")
            if href and not href.startswith("http"):
                href = "https://lostark.game.onstove.com" + href

            post_date = parse_lostark_date(title)
            if post_date and post_date < cutoff:
                continue

            if title:
                results.append({
                    "game": "로스트아크",
                    "type": "BM/캐시샵",
                    "title": title,
                    "date": date,
                    "link": href,
                })
    except Exception as e:
        print(f"  오류: {e}")
    return dedup_by_link(results)


# ─────────────────────────────────────────────
# 3. 아이온2
# ─────────────────────────────────────────────

def crawl_aion2(driver):
    """제목에 '외형 상품' 포함된 공지만 수집"""
    url = "https://aion2.plaync.com/ko-kr/board/notice/list"
    results = []
    try:
        soup = fetch_page(driver, url, "body", timeout=10)
        links = soup.select("a[href*='notice'], a[href*='board']")
        for a in links:
            href  = a.get("href", "")
            title = a.get_text(strip=True)
            if not href or not title or len(title) < 5:
                continue
            if not href.startswith("http"):
                href = "https://aion2.plaync.com" + href
            if not re.search(r"\d+", href):
                continue
            if "외형 상품" not in title:
                continue
            results.append({
                "game": "아이온2",
                "type": "BM/캐시샵",
                "title": title,
                "date": "",
                "link": href,
            })
    except Exception as e:
        print(f"  오류: {e}")
    return dedup_by_link(results)


# ─────────────────────────────────────────────
# 4. 마비노기 — 셀 카테고리 공지 + 2주 이내 + 박스/컬렉션
# ─────────────────────────────────────────────

def parse_mabinogi_date(date_str: str) -> datetime | None:
    """
    마비노기 날짜 포맷 파싱
    예: "26.03.26" → datetime(2026, 3, 26)
         "2026.03.26" → datetime(2026, 3, 26)
    """
    date_str = date_str.strip()
    # YY.MM.DD 포맷
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{2})$", date_str)
    if m:
        year  = 2000 + int(m.group(1))
        month = int(m.group(2))
        day   = int(m.group(3))
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    # YYYY.MM.DD 포맷
    m2 = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", date_str)
    if m2:
        try:
            return datetime(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
        except ValueError:
            return None
    return None

def crawl_mabinogi(driver):
    """
    마비노기 셀 카테고리 공지 (searchtype=91&searchword=셀)
    - 2주 이내 등록된 게시글만
    - 제목에 '박스' 또는 '컬렉션' 포함된 것만
    """
    url = "https://mabinogi.nexon.com/page/news/notice_list.asp?searchtype=91&searchword=%BC%A7"
    results = []
    cutoff = datetime.now() - timedelta(days=14)
    try:
        soup = fetch_page(driver, url, "body", timeout=15)

        # 공지 목록 행 파싱 — tr 또는 li 구조
        rows = soup.select("table.board_list tr, .notice_list tr, tbody tr, ul.list li")
        if not rows:
            rows = soup.select("tr, li")

        for row in rows:
            # 제목 링크
            title_el = row.select_one("td.subject a, td.title a, .tit a, a.subject, a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href  = title_el.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = "https://mabinogi.nexon.com" + href

            # 날짜 파싱
            date_el = row.select_one("td.date, td.regdate, .date, time, td:last-child")
            date_str = date_el.get_text(strip=True) if date_el else ""
            post_date = parse_mabinogi_date(date_str)

            # 2주 필터
            if post_date and post_date < cutoff:
                continue
            # 날짜 파싱 실패면 일단 포함 (제목 필터에서 걸러짐)

            # 제목 키워드 필터
            if "박스" not in title and "컬렉션" not in title:
                continue

            if title:
                results.append({
                    "game": "마비노기",
                    "type": "BM/캐시샵",
                    "title": title,
                    "date": date_str,
                    "link": href,
                })
    except Exception as e:
        print(f"  오류: {e}")
    return dedup_by_link(results)


# ─────────────────────────────────────────────
# 실행 & 저장
# ─────────────────────────────────────────────

def run_all():
    print("=" * 50)
    print(f"BM 모니터링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("\nChrome 드라이버 초기화 중...")
    driver = get_driver()
    all_results = []
    crawlers = [
        ("메이플 캐시샵 (외형)",      crawl_maple_cashshop),
        ("로스트아크 (상점/30일)",    crawl_lostark),
        ("아이온2 (외형 상품)",       crawl_aion2),
        ("마비노기 (박스/컬렉션/2주)", crawl_mabinogi),
    ]
    try:
        for name, fn in crawlers:
            print(f"\n[{name}] 수집 중...")
            data = fn(driver)
            print(f"  → {len(data)}건 수집")
            all_results.extend(data)
            sleep(1)
    finally:
        driver.quit()
        print("\nChrome 드라이버 종료")
    return all_results

def save_results(results):
    if not results:
        print("\n수집된 데이터 없음")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    df = pd.DataFrame(results)
    csv_path  = os.path.join(OUTPUT_DIR, f"bm_monitor_{timestamp}.csv")
    json_path = os.path.join(OUTPUT_DIR, f"bm_monitor_{timestamp}.json")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] {csv_path}")
    print(f"[저장] {json_path}")
    print("\n" + "=" * 50)
    summary = df.groupby(["game", "type"]).size().reset_index(name="count")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    results = run_all()
    save_results(results)
    try:
        from report import load_latest_json, generate_html, save_report
        data, src = load_latest_json()
        if data:
            save_report(generate_html(data, src), src)
            print("\nHTML 리포트 생성 완료! output/ 폴더에서 확인하세요.")
    except Exception as e:
        print(f"리포트 생성 실패: {e}")
