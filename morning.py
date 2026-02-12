import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import json

# =========================================================
# 🔑 사장님 전용 설정
# 1. 아래 따옴표 안에 발급받은 API 키를 붙여넣으세요.
MY_GEMINI_API_KEY = ""  
# =========================================================

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="위험도 분석 V0.59 (민감도 강화)", 
    page_icon="📊",
    layout="wide"
)

# --- 세션 상태 초기화 (API 키 유지용) ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = MY_GEMINI_API_KEY

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    html, body, p, h1, h2, h3, h4, div, span, label, li, a {
        font-family: 'Pretendard', sans-serif !important;
    }
    .header-title { font-size: 26px !important; font-weight: bold; color: #1e1e1e; margin-bottom: 5px; }
    .sub-info { font-size: 14px; color: #666; margin-bottom: 20px; }
    
    .mini-gauge-container {
        margin-bottom: 15px; padding: 12px; background-color: #fff; border-radius: 10px;
        border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .mini-gauge-title { font-size: 13px; font-weight: bold; color: #444; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
    .mini-gauge-track { position: relative; width: 100%; height: 8px; background-color: #f0f0f0; border-radius: 4px; }
    .mini-gauge-pointer {
        position: absolute; top: -5px; width: 10px; height: 18px; background-color: #222;
        border: 2px solid #fff; border-radius: 2px; transform: translateX(-50%);
    }
    .mini-gauge-labels { display: flex; justify-content: space-between; font-size: 10px; color: #aaa; margin-top: 4px; }
    
    /* 링크 스타일 */
    a { text-decoration: none; color: inherit; }
    a:hover { color: #1565c0; text-decoration: underline; }

    .guide-box { padding: 25px; background-color: #ffffff; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; color: #111 !important; }
    .guide-header { font-size: 20px; font-weight: 800; margin-bottom: 15px; color: #1565c0 !important; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
    .guide-section-title { font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; color: #1565c0 !important; }
    .guide-text { font-size: 15px; line-height: 1.7; margin-bottom: 10px; color: #333 !important; }
    .portfolio-card { background-color: #f0f4f8; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 5px solid #1565c0; }
    
    .news-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
    .news-title { font-weight: 600; text-decoration: none; color: #333; }
    .news-title:hover { color: #1565c0; text-decoration: underline; }
    .cal-badge { background-color: #fff3e0; color: #ef6c00; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 8px; }
    .semi-badge { background-color: #e3f2fd; color: #1565c0; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 8px; }
    
    .cal-time { font-weight: bold; color: #ef6c00; min-width: 45px; display: inline-block; }
    .cal-star { color: #ffca28; font-size: 12px; margin-left: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 위험도 분석 V0.59")
    
    api_input = st.text_input("🔑 Gemini API 키 입력", type="password", value=st.session_state.api_key, placeholder="여기에 키를 입력하세요")
    if api_input:
        st.session_state.api_key = api_input.strip()
        st.success("✅ API 키 적용됨")
        
    st.markdown("---")
    # [NEW] 수동 데이터 입력 섹션 추가
    with st.expander("🔧 수동 데이터 입력 (크롤링 실패 시)"):
        st.caption("자동 수집이 0으로 뜰 때, HTS나 네이버 금융을 보고 직접 입력하면 분석에 반영됩니다.")
        manual_kospi = st.number_input("KOSPI 외인 순매수 (억)", value=0, step=100)
        manual_kosdaq = st.number_input("KOSDAQ 외인 순매수 (억)", value=0, step=100)
    
    if st.button('🔄 데이터 새로고침'):
        st.rerun()
    
    if st.session_state.api_key:
        st.caption("AI 분석 모드가 활성화되었습니다.")
    else:
        st.info("ℹ️ 키가 없으면 기본 분석이 실행됩니다.")

# --- 데이터 수집 함수 ---
def get_weather(city="Daejeon"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t&_={int(time.time())}"
        res = requests.get(url, timeout=2)
        return res.text.strip() if res.status_code == 200 else "N/A"
    except: return "N/A"

# [수급 데이터] 수동 입력값 우선 적용 로직 추가
def get_market_investors(market_code="KOSPI"):
    headers = { 'User-Agent': 'Mozilla/5.0' }
    result = 0
    raw_val = "0"
    
    def parse_amount(text):
        try: 
            text = re.sub(r'[^\d\-]', '', text)
            return int(text) if text else 0
        except: return 0

    # 1차 시도: 네이버 금융 메인 (장중 실시간)
    try:
        url = f"https://finance.naver.com/sise/sise_index.naver?code={market_code}"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')
        
        # dl.lst_kos_info 구조 대응
        dts = soup.select('.lst_kos_info dt')
        dds = soup.select('.lst_kos_info dd')
        
        found = False
        for dt, dd in zip(dts, dds):
             if "외국인" in dt.text:
                 raw_val = dd.select_one('span').text.strip()
                 result = parse_amount(raw_val)
                 found = True
                 break

    except Exception as e: pass

    # 2차 시도: 값이 0이면 '일별 매매동향' 페이지 확인 (장 마감 후 확정치)
    if result == 0:
        try:
            sosok = '0' if market_code == "KOSPI" else '1'
            url_backup = f"https://finance.naver.com/sise/investor.naver?sosok={sosok}"
            res_backup = requests.get(url_backup, headers=headers, timeout=5)
            soup_backup = BeautifulSoup(res_backup.content.decode('euc-kr', 'replace'), 'html.parser')
            
            row = soup_backup.select_one('table.type_1 tr:nth-of-type(2)') 
            if row:
                cols = row.select('td')
                if len(cols) >= 3:
                    val_str_backup = cols[2].text.strip()
                    parsed_val = parse_amount(val_str_backup)
                    
                    if parsed_val != 0:
                        result = parsed_val
                        raw_val = val_str_backup
        except Exception as e: pass

    return {"val": result, "str": raw_val}

def get_economic_calendar():
    calendar_data = []
    try:
        url = "https://sslecal2.forexprostools.com/?columns=exc_flags,exc_currency,exc_importance,exc_actual,exc_forecast,exc_previous&features=datepicker,timezone&countries=5&calType=day&timeZone=88&lang=18"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        table = soup.select_one('#economicCalendarData')
        if not table: return []
        
        rows = table.select('tr')
        for row in rows:
            if not row.get('id', '').startswith('eventRowId'): continue
            
            time_str = row.select_one('.time').text.strip()
            event_name = row.select_one('.event').text.strip()
            sentiment_cell = row.select_one('.sentiment')
            importance = 0
            if sentiment_cell:
                importance = len(sentiment_cell.select('.grayFullBullishIcon'))
            
            if importance >= 2 or any(k in event_name for k in ["GDP", "CPI", "PCE", "고용", "금리", "연준", "FOMC", "판매"]):
                calendar_data.append({
                    'time': time_str,
                    'event': event_name,
                    'importance': importance
                })
            
    except Exception as e:
        pass
    return calendar_data

def get_financial_news():
    news = {"semi": []} 
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        search_url = "https://finance.naver.com/news/news_search.naver?q=%B9%DD%B5%B5%C3%BC" 
        res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')
        items = soup.select('.newsSchResult .newsList li dl')
        
        count = 0
        for item in items:
            at = item.select_one('.articleSubject a')
            if at:
                news["semi"].append({"title": at.text.strip(), "link": "https://finance.naver.com" + at['href']})
                count += 1
            if count >= 5: break
    except: pass
    
    return news

def get_all_data():
    tickers = {
        "tnx": "^TNX", "oil": "CL=F", "krw": "KRW=X",
        "nas": "^IXIC", "sp5": "^GSPC", "sox": "^SOX",
        "kospi": "^KS11", "kosdaq": "^KQ11",
        "gold": "GC=F", "silver": "SI=F", "btc": "BTC-USD", "vix": "^VIX"
    }
    data = {}
    try:
        for key, symbol in tickers.items():
            df = yf.download(symbol, period="10d", progress=False) # 10일치로 늘려서 추세 확인
            if len(df) < 2: df = pd.concat([df, df])
            
            # 최신값
            curr = df['Close'].iloc[-1].item() if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1]
            # 전일값
            prev = df['Close'].iloc[-2].item() if isinstance(df['Close'].iloc[-2], pd.Series) else df['Close'].iloc[-2]
            
            # 5일 최고가 (추세 확인용)
            high_5d = df['Close'].iloc[-5:].max().item() if len(df) >= 5 else curr
            
            diff = curr - prev
            pct = (diff / prev) * 100
            
            # 고점 대비 하락률 (Drawdown) - 양수로 변환 (예: 5% 하락이면 5.0)
            dd = ((high_5d - curr) / high_5d) * 100 if high_5d > 0 else 0
            
            data[key] = {'val': curr, 'diff': diff, 'pct': pct, 'dd': dd}
        return data, None
    except Exception as e: return None, e

# --- 기본 분석 알고리즘 ---
def get_basic_report(m, inv_kospi, inv_kosdaq, score, news, calendar):
    res = {"headline": "", "portfolio": ""}
    
    if score >= 70: res["headline"] = "🚨 [매우 위험] 현금 100% 확보 권장. 소나기는 피해야 합니다."
    elif score >= 50: res["headline"] = "⚠️ [경계] 시장 변동성 확대. 방어적 포지션 및 헷지 필요."
    elif score >= 30: res["headline"] = "⚖️ [혼조세] 방향성 탐색 구간. 주도주 위주의 선별적 접근."
    else: res["headline"] = "⛅ [양호] 투자 심리 안정. 조정 시 매수 관점 유효."

    top_issue = ""
    if calendar:
        sorted_cal = sorted(calendar, key=lambda x: (-x['importance'], x['time']))
        top_event = sorted_cal[0]
        top_issue = f"오늘밤 {top_event['event']} 발표"
    elif news['semi']:
        top_issue = news['semi'][0]['title']
    
    if top_issue:
        if len(top_issue) > 35: top_issue = top_issue[:35] + "..."
        res["headline"] += f"<br><span style='font-size:15px; color:#1565c0; font-weight:normal;'>📢 주요 이슈: {top_issue}</span>"

    lines = []
    
    # 반도체 - 추세(dd)까지 고려
    if m['sox']['pct'] > 1.5: lines.append("✅ <b>반도체:</b> 필라델피아 반도체 급등. 대형주 중심 비중 확대.")
    elif m['sox']['dd'] > 3.0: lines.append(f"⚠️ <b>반도체:</b> 단기 고점 대비 {m['sox']['dd']:.1f}% 조정 중. 섣부른 매수 자제.")
    else: lines.append("⏺ <b>반도체:</b> 방향성 탐색 중. 외인 수급 확인 후 분할 대응.")

    # 코스피 수급 코멘트
    if inv_kospi['val'] > 0: lines.append(f"💰 <b>코스피:</b> 외국인 {abs(inv_kospi['val'])}억 순매수. 수급 양호.")
    elif inv_kospi['val'] < 0: lines.append(f"💸 <b>코스피:</b> 외국인 {abs(inv_kospi['val'])}억 순매도. 환율/수급 부담.")

    # 코스닥 수급 코멘트 추가
    if inv_kosdaq['val'] > 0: lines.append(f"📈 <b>코스닥:</b> 외국인 {abs(inv_kosdaq['val'])}억 순매수. 개별주 장세.")
    else: lines.append(f"📉 <b>코스닥:</b> 외국인 {abs(inv_kosdaq['val'])}억 순매도. 리스크 관리.")

    if m['gold']['pct'] > 0.5 or m['vix']['val'] > 18: lines.append("🟡 <b>전략:</b> 시장 불안감 상존. 금/달러 등 헷지 자산 관심.")

    res["portfolio"] = "<br>".join(lines)
    return res

# --- AI 분석 함수 ---
def get_ai_portfolio_analysis(api_key, m, inv_kospi, inv_kosdaq, score, news_titles, calendar_str):
    if not api_key: return None
    
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""당신은 20년 경력의 펀드매니저입니다.
    현재 자체 알고리즘으로 산출된 시장 위험도는 {score}점(100점 만점)입니다.
    (점수가 높을수록 위험, 50점 이상이면 경계 단계)
    
    [핵심 지표]
    - 미국채 10년물: {m['tnx']['val']:.2f}% (전일대비 {m['tnx']['diff']:.2f})
    - 원/달러 환율: {m['krw']['val']:.0f}원
    - 필라델피아 반도체: {m['sox']['pct']:.2f}% 등락 (고점 대비 {m['sox']['dd']:.1f}% 하락 중)
    - 외국인 코스피: {inv_kospi['val']}억원
    - 외국인 코스닥: {inv_kosdaq['val']}억원
    
    [오늘 주요 일정]
    {calendar_str}
    
    [뉴스 헤드라인]
    {news_titles}

    위 데이터를 종합하여 투자 가이드를 JSON으로 작성해주세요.
    말투는 간결하고 전문적으로(해요체).
    JSON 키: "headline"(시장 총평, 이모지 포함), "portfolio"(구체적 전략, HTML 태그 사용 가능)
    """
    
    last_error = ""
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
        try:
            res = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match: return json.loads(match.group(0))
            else:
                last_error = f"{res.status_code}"
                continue
        except Exception as e:
            last_error = str(e)
            continue
            
    return {"error": f"AI 연결 실패. Error: {last_error}"}

# --- 실행부 ---
weather = get_weather()
kst_now = datetime.utcnow() + timedelta(hours=9)
st.markdown(f"""<div class="header-title">📊 위험도 분석 V0.59 (민감도↑)</div><div class="sub-info">📍 대전: {weather} | 🕒 {kst_now.strftime('%Y-%m-%d %H:%M')} (한국시간)</div>""", unsafe_allow_html=True)

data, err = get_all_data()
inv_kospi = get_market_investors("KOSPI")
inv_kosdaq = get_market_investors("KOSDAQ")

# [수정] 수동 입력값 우선 적용
if 'manual_kospi' in locals() and manual_kospi != 0:
    inv_kospi = {"val": manual_kospi, "str": f"{manual_kospi}억(수동)"}
if 'manual_kosdaq' in locals() and manual_kosdaq != 0:
    inv_kosdaq = {"val": manual_kosdaq, "str": f"{manual_kosdaq}억(수동)"}

news = get_financial_news()
calendar = get_economic_calendar() 

if data:
    def mini_gauge(title, d, min_v, max_v, mode='risk', unit='', url_key=None):
        val = d['val']
        pct = max(0, min(100, (val - min_v) / (max_v - min_v) * 100))
        grad = "linear-gradient(90deg, #4CAF50 0%, #FFEB3B 50%, #F44336 100%)" if mode=='risk' else "linear-gradient(90deg, #2196F3 0%, #EEEEEE 50%, #F44336 100%)"
        
        display_title = title
        if url_key and url_key in chart_urls:
            display_title = f'<a href="{chart_urls[url_key]}" target="_blank" title="차트 보기">{title} <span style="font-size:10px;">🔗</span></a>'
        
        st.markdown(f"""<div class="mini-gauge-container"><div class="mini-gauge-title"><span>{display_title}</span><span>{val:,.2f}{unit} ({d['pct']:+.2f}%)</span></div><div class="mini-gauge-track" style="background:{grad}"><div class="mini-gauge-pointer" style="left:{pct}%"></div></div><div class="mini-gauge-labels"><span>{min_v}</span><span>{max_v}</span></div></div>""", unsafe_allow_html=True)

    chart_urls = {
        "tnx": "https://finance.yahoo.com/quote/%5ETNX", "oil": "https://finance.yahoo.com/quote/CL=F",
        "krw": "https://finance.yahoo.com/quote/KRW=X", "nas": "https://finance.yahoo.com/quote/%5EIXIC",
        "sp5": "https://finance.yahoo.com/quote/%5EGSPC", "sox": "https://finance.yahoo.com/quote/%5ESOX",
        "kospi": "https://finance.yahoo.com/quote/%5EKS11", "kosdaq": "https://finance.yahoo.com/quote/%5EKQ11",
        "gold": "https://finance.yahoo.com/quote/GC=F", "silver": "https://finance.yahoo.com/quote/SI=F",
        "btc": "https://finance.yahoo.com/quote/BTC-USD", "vix": "https://finance.yahoo.com/quote/%5EVIX"
    }

    # 섹션 1: 주요 지표 현황
    st.subheader("📈 주요 지표 현황")
    c1, c2, c3 = st.columns(3)
    with c1:
        mini_gauge("🇺🇸 국채 10년", data['tnx'], 3.2, 4.8, 'risk', '%', 'tnx') # 범위 축소 (3.0~5.0 -> 3.2~4.8)
        mini_gauge("🇺🇸 나스닥", data['nas'], 15000, 30000, 'stock', url_key='nas') 
        mini_gauge("🇰🇷 코스피", data['kospi'], 2000, 3000, 'stock', url_key='kospi') # 범위 현실화
    with c2:
        mini_gauge("🛢️ WTI 유가", data['oil'], 60, 90, 'risk', '$', 'oil')
        mini_gauge("🇺🇸 S&P 500", data['sp5'], 4500, 7000, 'stock', url_key='sp5')
        mini_gauge("🇰🇷 코스닥", data['kosdaq'], 600, 1000, 'stock', url_key='kosdaq') # 범위 현실화
    with c3:
        mini_gauge("🇰🇷 환율", data['krw'], 1250, 1450, 'risk', '원', 'krw') # 범위 강화 (1300~1500 -> 1250~1450)
        mini_gauge("💾 반도체(SOX)", data['sox'], 3000, 6000, 'stock', url_key='sox') 
        
        # 코스피/코스닥 외국인 수급 표시
        k_val = inv_kospi['str']
        k_color = "#d32f2f" if inv_kospi['val'] < 0 else "#1565c0" 
        kq_val = inv_kosdaq['str']
        kq_color = "#d32f2f" if inv_kosdaq['val'] < 0 else "#1565c0"
        
        st.markdown(f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; margin-top:5px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-size:13px; color:#333;"><b>코스피 外</b></span>
                <span style="font-size:14px; font-weight:bold; color:{k_color};">{k_val}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="font-size:13px; color:#333;"><b>코스닥 外</b></span>
                <span style="font-size:14px; font-weight:bold; color:{kq_color};">{kq_val}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 섹션 2: 대체 자산 & 공포지수
    st.subheader("🛡️ 대체 자산 & 공포지수")
    c7, c8, c9, c10 = st.columns(4)
    with c7: mini_gauge("🟡 금(Gold)", data['gold'], 2000, 4000, 'stock', '$', 'gold') 
    with c8: mini_gauge("⚪ 은(Silver)", data['silver'], 20, 50, 'stock', '$', 'silver') 
    with c9: mini_gauge("₿ 비트코인", data['btc'], 50000, 150000, 'stock', '$', 'btc') 
    with c10: mini_gauge("😨 VIX(공포)", data['vix'], 12, 30, 'risk', url_key='vix') # 범위 강화 (15~35 -> 12~30)

    # --- 위험도 산정 로직 강화 (V0.59) ---
    def calc_r(v, min_v, max_v): return max(0, min(100, (v - min_v) / (max_v - min_v) * 100))
    
    # [수정 포인트]
    # 1. 환율(KRW) 기준을 1280원으로 낮춤 (1350은 너무 관대함) -> 현재 1400원이면 점수 대폭 상승
    # 2. 반도체(SOX)와 시장(KOSPI)은 '전일 등락'이 아니라 '5일 고점 대비 하락폭(dd)'을 사용해 추세 반영
    # 3. 외국인 수급은 매도 규모에 대한 민감도를 2배 높임 (/20 -> /10)
    
    risk_factors = {
        'tnx': calc_r(data['tnx']['val'], 3.2, 4.8),     # 국채 금리: 3.2% 이상부터 위험 인식
        'oil': calc_r(data['oil']['val'], 65, 90),       # 유가
        'krw': calc_r(data['krw']['val'], 1280, 1450),   # 환율: 1280원부터 위험 카운트 (중요)
        'vix': calc_r(data['vix']['val'], 12, 30),       # 공포지수: 12부터 민감하게 반응
        'sox': calc_r(data['sox']['dd'], 0, 6),          # 반도체: 고점대비 6% 빠지면 만점 (추세 반영)
        'mkt': calc_r(data['kospi']['dd'], 0, 5),        # 코스피: 고점대비 5% 빠지면 만점
        'inv': calc_r(-(inv_kospi['val'] + inv_kosdaq['val'])/10, 0, 500) # 수급: 5000억 매도시 만점
    }
    
    # 가중치 부여 (환율과 반도체, 수급이 한국장엔 깡패임)
    weighted_score = (
        risk_factors['tnx'] * 1.0 +
        risk_factors['oil'] * 0.5 +
        risk_factors['krw'] * 1.5 +  # 환율 가중치 1.5배
        risk_factors['vix'] * 1.0 +
        risk_factors['sox'] * 1.5 +  # 반도체 심리 가중치 1.5배
        risk_factors['mkt'] * 1.0 +
        risk_factors['inv'] * 1.5    # 수급 가중치 1.5배
    ) / 8.0 # 가중치 총합
    
    risk_score = int(weighted_score)
    
    # 위험도 색상 표시
    score_color = "#4CAF50" # Green
    if risk_score >= 70: score_color = "#D32F2F" # Red
    elif risk_score >= 50: score_color = "#FF9800" # Orange
    elif risk_score >= 30: score_color = "#FFC107" # Yellow
    
    st.subheader(f"📊 종합 시장 위험도: : {risk_score}점")
    st.markdown(f"""
    <div style="width:100%; height:20px; background:#eee; border-radius:10px; margin-bottom:10px;">
        <div style="width:{risk_score}%; height:100%; background:{score_color}; border-radius:10px; transition:1s;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 보고서 출력 ---
    news_summary = " / ".join([n['title'] for n in news['semi'][:3]])
    calendar_str = "\n".join([f"{c['time']} {c['event']} (★{c['importance']})" for c in calendar])
    
    ai_report = get_ai_portfolio_analysis(st.session_state.api_key, data, inv_kospi, inv_kosdaq, risk_score, news_summary, calendar_str)
    
    is_error = False
    error_msg = ""
    if ai_report and "error" in ai_report:
        is_error = True
        error_msg = ai_report['error']
        ai_report = None

    mode_label = "🤖 AI 애널리스트" if ai_report else "⚙️ 기본 분석 엔진"
    if not ai_report: 
        ai_report = get_basic_report(data, inv_kospi, inv_kosdaq, risk_score, news, calendar)
        if is_error: st.error(f"AI 연결 실패 ({error_msg}). 기본 분석 모드로 전환합니다.") 
    
    st.markdown(f"""
    <div class="guide-box">
        <div class="guide-header">📊 {mode_label} 브리핑</div>
        <div class="guide-section-title">1. 시장 총평</div>
        <div class="guide-text"><b>{ai_report.get('headline', '분석 실패')}</b></div>
        <div class="guide-section-title">2. 주식 운영 가이드</div>
        <div class="portfolio-card">{ai_report.get('portfolio', '데이터 분석 실패').replace('\\n', '<br>')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    n1, n2 = st.columns(2)
    with n1:
        st.markdown("### 🇺🇸 오늘 주요 경제 일정 (미국)")
        st.caption("📅 [전체 일정 보기](https://kr.investing.com/economic-calendar/) (Investing.com)")
        
        if not calendar:
            st.info("오늘 예정된 주요 미국 경제 지표 발표가 없거나 데이터를 가져오지 못했습니다.")
        else:
            sorted_cal = sorted(calendar, key=lambda x: x['time'])
            for event in sorted_cal:
                stars = "★" * event['importance']
                st.markdown(f"""
                <div class="news-item">
                    <span class="cal-badge">Event</span>
                    <span class="cal-time">{event['time']}</span>
                    <span class="news-title">{event['event']}</span>
                    <span class="cal-star">{stars}</span>
                </div>
                """, unsafe_allow_html=True)
                
    with n2:
        st.markdown("### 🇰🇷 국내 반도체(Semi) 뉴스")
        if not news['semi']: st.info("관련된 최신 뉴스가 없습니다.")
        for n in news['semi']: st.markdown(f"""<div class="news-item"><span class="semi-badge">Chip</span><a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a></div>""", unsafe_allow_html=True)

time.sleep(300)
st.rerun()
