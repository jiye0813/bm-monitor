# 🕵️ 경쟁사 외형 BM 모니터링 크롤러

> 주요 MMORPG의 외형 BM 관련 공지를 자동 수집하고 HTML 리포트로 시각화하는 툴

---

## 만든 이유

BM 기획 업무에서 경쟁사 분석은 필수지만, 게임별로 공식 사이트를 하나씩 들어가며 확인하는 과정이 반복적이고 비효율적이었습니다. 특히 외형 아이템 신규 출시나 프로모션 타이밍을 놓치면 자사 BM 전략에도 영향을 주기 때문에, 외형 BM 관련 정보만 정확하게 걸러서 자동 수집하고 HTML 리포트로 뽑아주는 툴을 직접 제작했습니다.

---

## 수집 대상 및 필터링 조건

| 게임 | 수집 URL | 필터링 조건 |
|------|----------|------------|
| 메이플스토리 | maplestory.nexon.com/News/CashShop | 제목에 코디·헤어·성형·로얄·의상·스타일 등 외형 키워드 포함된 것만 |
| 로스트아크 | lostark.game.onstove.com/News/Notice/List?noticetype=shop | 말머리 "상점" + 작성일 기준 30일 이내 |
| 아이온2 | aion2.plaync.com/ko-kr/board/notice/list | 제목에 "외형 상품" 포함된 것만 |

---

## 주요 기능

### 게임별 맞춤 필터링
단순 크롤링이 아니라 각 게임의 BM 구조에 맞게 필터 조건을 다르게 적용했어요.
- 메이플은 캐시샵 공지 중 외형 관련만 → 강화 스크롤, 편의 아이템 등 노이즈 자동 제외
- 로스트아크는 말머리 "상점" 글만 + 30일 초과 오래된 공지 자동 제외
- 아이온2는 "외형 상품" 키워드가 제목에 있는 공지만

### URL 끝 숫자 기준 정렬
각 게임 공지의 URL 끝 번호가 클수록 최신 등록이므로, 이를 기준으로 내림차순 정렬합니다.

### HTML 리포트 자동 생성
`crawler.py` 실행 시 수집 직후 HTML 리포트를 자동 생성합니다.
- 전체 / BM / 이벤트 수 요약 카드
- 게임별 탭 필터
- 유형별 필터 (BM/캐시샵, 이벤트, 업데이트, 공지)
- 각 항목 바로가기 링크
- 게임별 색상 구분

### 결과 저장
- `output/bm_monitor_YYYYMMDD_HHMM.csv`
- `output/bm_monitor_YYYYMMDD_HHMM.json`
- `output/bm_monitor_YYYYMMDD_HHMM_report.html`

---

## 설치 및 실행

```bash
# 1. 레포 클론
git clone https://github.com/jiye0813/bm-monitor.git
cd bm-monitor

# 2. 패키지 설치
pip install -r requirements.txt

# 3-A. 즉시 1회 실행 (크롤링 + HTML 리포트 자동 생성)
python crawler.py

# 3-B. 리포트만 다시 생성 (기존 JSON 기반)
python report.py

# 3-C. 매일 오전 9시 자동 실행
python scheduler.py
```

실행 후 `output/` 폴더의 `_report.html` 파일을 브라우저로 열면 리포트를 확인할 수 있습니다.

---

## 기술 스택

- Python 3.11+
- Selenium + webdriver-manager — JavaScript 렌더링 페이지 크롤링
- BeautifulSoup4 — HTML 파싱
- pandas — 데이터 처리 및 CSV 저장
- schedule — 자동 실행 스케줄링

---

## 파일 구조

```
bm-monitor/
├── crawler.py       # 메인 크롤러 (게임별 수집 + 리포트 자동 생성)
├── report.py        # HTML 리포트 생성기 (단독 실행 가능)
├── scheduler.py     # 매일 자동 실행 스케줄러
├── requirements.txt
└── output/          # 수집 결과 저장 폴더 (자동 생성)
    ├── bm_monitor_YYYYMMDD_HHMM.csv
    ├── bm_monitor_YYYYMMDD_HHMM.json
    └── bm_monitor_YYYYMMDD_HHMM_report.html
```

---

## 제작자

**석지예** · 게임 사업 PM

- 📧 jiye0813@naver.com
- 🔗 [포트폴리오](https://www.notion.so/PM-26db3b5bd8e38065bc68fe3aa61283a0)
- 🔗 [마비노기 의장 대시보드](https://jiye0813.github.io/mabinogi-dress/)
- 🔗 [BM 매출 예측 시뮬레이터](https://jiye0813.github.io/bm-simulator/)
