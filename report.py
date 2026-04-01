"""
BM 모니터링 결과 → HTML 리포트 생성기
crawler.py 실행 후 자동 호출되거나 단독 실행 가능
"""

import json
import os
import glob
from datetime import datetime

OUTPUT_DIR = "output"

GAME_COLORS = {
    "메이플스토리":   {"bg": "#E8F4FD", "accent": "#1A6BB5"},
    "로스트아크":     {"bg": "#FDF0E8", "accent": "#C45E1A"},
    "아이온2":        {"bg": "#EDF5ED", "accent": "#2E7D32"},
    "파이널판타지14": {"bg": "#F3EDF7", "accent": "#6A1B9A"},
}

TYPE_BADGE = {
    "BM/캐시샵": ("🎰", "#1A6BB5", "#E8F4FD"),
    "이벤트":    ("🎉", "#B55A1A", "#FDF0E8"),
    "업데이트":  ("🔧", "#2E7D32", "#EDF5ED"),
    "공지":      ("📢", "#555555", "#F5F5F5"),
}

def load_latest_json():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "bm_monitor_*.json")), reverse=True)
    if not files:
        print("output/ 폴더에 JSON 파일이 없어요. crawler.py를 먼저 실행해주세요.")
        return None, None
    path = files[0]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path

def make_badge(type_str):
    icon, color, bg = TYPE_BADGE.get(type_str, ("📌", "#555", "#eee"))
    return f'<span class="badge" style="background:{bg};color:{color};">{icon} {type_str}</span>'

def make_game_badge(game):
    c = GAME_COLORS.get(game, {"accent": "#555", "bg": "#eee"})
    return f'<span class="badge" style="background:{c["bg"]};color:{c["accent"]};border:1px solid {c["accent"]}33;">{game}</span>'

def generate_html(data, source_path):
    now   = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    total = len(data)
    games = list(dict.fromkeys(d["game"] for d in data))

    game_counts, type_counts = {}, {}
    for d in data:
        game_counts[d["game"]] = game_counts.get(d["game"], 0) + 1
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1

    bm_cnt    = type_counts.get("BM/캐시샵", 0)
    event_cnt = type_counts.get("이벤트", 0)

    summary = f"""
    <div class="summary-grid">
      <div class="summary-card"><div class="summary-num">{total}</div><div class="summary-label">전체 수집</div></div>
      <div class="summary-card accent-blue"><div class="summary-num">{bm_cnt}</div><div class="summary-label">BM/캐시샵</div></div>
      <div class="summary-card accent-orange"><div class="summary-num">{event_cnt}</div><div class="summary-label">이벤트</div></div>
      <div class="summary-card accent-green"><div class="summary-num">{len(games)}</div><div class="summary-label">모니터링 게임</div></div>
    </div>"""

    tab_btns = '<button class="tab-btn active" onclick="filterGame(\'all\',this)">전체</button>'
    for g in games:
        tab_btns += f'<button class="tab-btn" onclick="filterGame(\'{g}\',this)">{g} <span class="tab-cnt">{game_counts.get(g,0)}</span></button>'

    cards_html = ""
    for d in data:
        game  = d.get("game","")
        title = d.get("title","")
        date  = d.get("date","")
        link  = d.get("link","")
        dtype = d.get("type","공지")
        gc    = GAME_COLORS.get(game,{"accent":"#555","bg":"#f5f5f5"})
        link_html = f'<a href="{link}" target="_blank" class="card-link">바로가기 →</a>' if link else ""
        date_html = f'<span class="card-date">{date}</span>' if date else ""
        cards_html += f"""
        <div class="item-card" data-game="{game}" data-type="{dtype}">
          <div class="card-header" style="border-left:4px solid {gc['accent']};">
            <div class="card-title">{title}</div>
            <div class="card-meta">{make_game_badge(game)}{make_badge(dtype)}{date_html}</div>
          </div>
          {link_html}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BM 모니터링 리포트 — {now}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;background:#f7f7f5;color:#1a1a1a;}}
  .header{{background:#1a1a1a;color:white;padding:2rem;}}
  .header h1{{font-size:20px;font-weight:500;margin-bottom:4px;}}
  .header p{{font-size:13px;color:#aaa;}}
  .container{{max-width:960px;margin:0 auto;padding:2rem 1rem;}}
  .summary-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:2rem;}}
  .summary-card{{background:white;border-radius:12px;padding:1.25rem;border:0.5px solid #e0e0e0;}}
  .summary-num{{font-size:32px;font-weight:500;}}
  .summary-label{{font-size:13px;color:#888;margin-top:4px;}}
  .accent-blue .summary-num{{color:#1A6BB5;}}
  .accent-orange .summary-num{{color:#C45E1A;}}
  .accent-green .summary-num{{color:#2E7D32;}}
  .tab-bar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:1rem;}}
  .tab-btn{{padding:6px 14px;border-radius:20px;border:0.5px solid #ddd;background:white;font-size:13px;cursor:pointer;color:#555;}}
  .tab-btn.active{{background:#1a1a1a;color:white;border-color:#1a1a1a;}}
  .tab-cnt{{font-size:11px;opacity:0.7;}}
  .filter-bar{{display:flex;gap:8px;margin-bottom:1.25rem;flex-wrap:wrap;}}
  .filter-btn{{padding:4px 12px;border-radius:20px;border:0.5px solid #ddd;background:white;font-size:12px;cursor:pointer;color:#555;}}
  .filter-btn.active{{background:#555;color:white;border-color:#555;}}
  .item-card{{background:white;border-radius:12px;margin-bottom:10px;border:0.5px solid #e8e8e8;overflow:hidden;}}
  .item-card:hover{{box-shadow:0 2px 12px rgba(0,0,0,0.08);}}
  .card-header{{padding:1rem 1.25rem 0.75rem;}}
  .card-title{{font-size:15px;font-weight:500;margin-bottom:8px;line-height:1.4;}}
  .card-meta{{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}}
  .badge{{font-size:11px;font-weight:500;padding:2px 8px;border-radius:20px;}}
  .card-date{{font-size:12px;color:#999;}}
  .card-link{{display:block;padding:8px 1.25rem;font-size:13px;color:#1A6BB5;border-top:0.5px solid #f0f0f0;text-decoration:none;}}
  .card-link:hover{{background:#f7f9fc;}}
  .hidden{{display:none;}}
  .foot{{font-size:12px;color:#bbb;margin-top:2rem;text-align:center;}}
  @media(max-width:600px){{.summary-grid{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<div class="header">
  <h1>경쟁사 외형 BM 모니터링 리포트</h1>
  <p>수집일시: {now} &nbsp;|&nbsp; 출처: {os.path.basename(source_path)}</p>
</div>
<div class="container">
  {summary}
  <div class="tab-bar">{tab_btns}</div>
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterType('all',this)">전체 유형</button>
    <button class="filter-btn" onclick="filterType('BM/캐시샵',this)">🎰 BM/캐시샵</button>
    <button class="filter-btn" onclick="filterType('이벤트',this)">🎉 이벤트</button>
    <button class="filter-btn" onclick="filterType('업데이트',this)">🔧 업데이트</button>
    <button class="filter-btn" onclick="filterType('공지',this)">📢 공지</button>
  </div>
  <div id="card-list">{cards_html}</div>
  <p class="foot">generated by bm-monitor · {now}</p>
</div>
<script>
let cGame='all',cType='all';
function filterGame(g,btn){{cGame=g;document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');apply();}}
function filterType(t,btn){{cType=t;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');apply();}}
function apply(){{document.querySelectorAll('.item-card').forEach(c=>{{const gm=cGame==='all'||c.dataset.game===cGame;const tm=cType==='all'||c.dataset.type===cType;c.classList.toggle('hidden',!(gm&&tm));}});}}
</script>
</body>
</html>"""

def save_report(html, source_path):
    base = os.path.basename(source_path).replace(".json","")
    path = os.path.join(OUTPUT_DIR, f"{base}_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[리포트 저장] {path}")
    return path

if __name__ == "__main__":
    data, src = load_latest_json()
    if data:
        html = generate_html(data, src)
        save_report(html, src)
        print("output/ 폴더의 _report.html 파일을 브라우저로 열어주세요!")
