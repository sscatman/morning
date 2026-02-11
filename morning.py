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
    page_title="위험도 분석 V0.56", 
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
    .portfolio-item { margin-bottom: 8px; font-size: 14.5px; line-height: 1.6; }
    
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
    st.header("⚙️ 위험도 분석 V0.55")
    
    api_input = st.text_input("🔑 Gemini API 키 입력", type="password", value=st.session_state.api_key, placeholder="여기에 키를 입력하세요")
    
    if api_input:
        st.session_state.api_key = api_input.strip()
        st.success("✅ API 키 적용됨")
    
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

# [핵심 수정] 수급 데이터 2중 체크 (0일 경우 백업 페이지 확인)
def get_market_investors():
    headers = { 'User-Agent': 'Mozilla/5.0' }
    result = { "kospi_foreigner": 0, "raw_data": {"kospi_foreigner": "0"} }
    
    def parse_amount(text):
        try: 
            text = re.sub(r'[^\d\-]', '', text)
            return int(text) if text else 0
        except: return 0

    # 1차 시도: 네이버 금융 메인 (장중 실시간)
    try:
        url_kospi = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
        res_kospi = requests.get(url_kospi, headers=headers, timeout=5)
        soup_kospi = BeautifulSoup(res_kospi.content.decode('euc-kr', 'replace'), 'html.parser')
        
        investor_list = soup_kospi.select('.lst_kos_info li')
        found = False
        for item in investor_list:
            title = item.select_one('dt').text.strip()
            if "외국인" in title:
                val_str = item.select_one('dd span').text.strip()
                result["kospi_foreigner"] = parse_amount(val_str)
                result["raw_data"]["kospi_foreigner"] = val_str
                found = True
                break
        
        if not found:
             dts = soup_kospi.select('.lst_kos_info dt')
             dds = soup_kospi.select('.lst_kos_info dd')
             for dt, dd in zip(dts, dds):
                 if "외국인" in dt.text:
                     val_str = dd.select_one('span').text.strip()
                     result["kospi_foreigner"] = parse_amount(val_str)
                     result["raw_data"]["kospi_foreigner"] = val_str
                     break

    except Exception as e: pass

    # 2차 시도: 값이 0이면 '일별 매매동향' 페이지 확인 (장 마감 후 확정치)
    if result["kospi_foreigner"] == 0:
        try:
            url_backup = "https://finance.naver.com/sise/investor.naver"
            res_backup = requests.get(url_backup, headers=headers, timeout=5)
            soup_backup = BeautifulSoup(res_backup.content.decode('euc-kr', 'replace'), 'html.parser')
            
            # 테이블의 첫 번째 데이터 행 찾기 (오늘 날짜)
            # 보통 날짜 | 개인 | 외국인 | 기관 순서
            row = soup_backup.select_one('table.type_1 tr:nth-of-type(2)') 
            if row:
                cols = row.select('td')
                if len(cols) >= 3:
                    # 인덱스 0: 날짜, 1: 개인, 2: 외국인, 3: 기관
                    val_str_backup = cols[2].text.strip()
                    parsed_val = parse_amount(val_str_backup)
                    
                    if parsed_val != 0:
                        result["kospi_foreigner"] = parsed_val
                        result["raw_data"]["kospi_foreigner"] = val_str_backup
        except Exception as e: pass

    return result

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
            df = yf.download(symbol, period="5d", progress=False)
            if len(df) < 2: df = pd.concat([df, df])
            curr = df['Close'].iloc[-1].item() if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2].item() if isinstance(df['Close'].iloc[-2], pd.Series) else df['Close'].iloc[-2]
            diff = curr - prev
            pct = (diff / prev) * 100
            data[key] = {'val': curr, 'diff': diff, 'pct': pct}
        return data, None
    except Exception as e: return None, e

# --- 기본 분석 알고리즘 ---
def get_basic_report(m, inv, score, news, calendar):
    res = {"headline": "", "portfolio": ""}
    
    if score >= 60: res["headline"] = "🚨 고위험 국면입니다. 자산 보호를 최우선으로 해야 합니다."
    elif score >= 40: res["headline"] = "⚖️ 변동성이 큰 혼조세입니다. 방어적인 포지션이 유리합니다."
    elif score >= 20: res["headline"] = "⛅ 완만한 흐름입니다. 주도주 중심의 선별적 대응이 필요합니다."
    else: res["headline"] = "☀️ 시장 에너지가 매우 좋습니다. 적극적인 투자 기회입니다."

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
    if m['sox']['pct'] > 1: lines.append("✅ <b>반도체:</b> 필라델피아 반도체 강세. 삼성전자/SK하이닉스 등 대형주 중심 접근 유효.")
    elif m['sox']['pct'] < -2: lines.append("⚠️ <b>반도체:</b> 지수 급락으로 인한 투자 심리 위축. 보수적 관망 필요.")
    else: lines.append("⏺ <b>반도체:</b> 뚜렷한 방향성 부재. 외인 수급 동향을 살피며 분할 대응.")

    if inv['kospi_foreigner'] > 0: lines.append(f"💰 <b>수급:</b> 외국인이 코스피를 {abs(inv['kospi_foreigner'])}억 순매수 중입니다. 대형주에 긍정적입니다.")
    elif inv['kospi_foreigner'] < 0: lines.append(f"💸 <b>수급:</b> 외국인이 코스피를 {abs(inv['kospi_foreigner'])}억 순매도 중입니다. 환율 변동성에 주의하세요.")

    if m['nas']['pct'] > 0: lines.append("🚀 <b>미국:</b> 기술주 중심의 상승세 지속. AI 및 성장주 섹터 비중 유지.")
    else: lines.append("⏺ <b>미국:</b> 금리 및 매크로 변수로 인한 숨고르기 장세.")

    if m['gold']['pct'] > 0.5 or m['vix']['val'] > 20: lines.append("🟡 <b>헷지:</b> 시장 불안정성 확대 가능성. 금/달러 등 안전자산 일부 편입 고려.")

    res["portfolio"] = "<br>".join(lines)
    return res

# --- AI 분석 함수 ---
def get_ai_portfolio_analysis(api_key, m, inv, score, news_titles, calendar_str):
    if not api_key: return None
    
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""당신은 월스트리트 출신의 전문 펀드매니저입니다. 
    현재 시장 위험도는 {score}점(100점 만점)입니다.
    
    [시장 데이터]
    - 미국채 10년물: {m['tnx']['val']:.2f}%
    - 환율: {m['krw']['val']:.0f}원
    - 필라델피아 반도체: {m['sox']['pct']:.2f}% 변동
    - 외국인 코스피 수급: {inv['kospi_foreigner']}억원 (양수면 매수, 음수면 매도)
    
    [오늘 주요 경제 일정 (미국)]
    {calendar_str}
    
    [주요 뉴스]
    {news_titles}

    위 데이터를 바탕으로 JSON 형식의 투자 가이드를 작성해주세요.
    JSON 키: "headline"(시장 총평, 이모지 포함 한줄), "portfolio"(구체적 대응 전략 및 섹터 추천, HTML 태그 사용 가능)
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
st.markdown(f"""<div class="header-title">📊 위험도 분석 V0.55</div><div class="sub-info">📍 대전: {weather} | 🕒 {kst_now.strftime('%Y-%m-%d %H:%M')} (한국시간)</div>""", unsafe_allow_html=True)

data, err = get_all_data()
inv = get_market_investors()
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
        # 미국채 10년물: 최대치 5.5 -> 5.0 수정
        mini_gauge("🇺🇸 국채 10년", data['tnx'], 3.0, 5.0, 'risk', '%', 'tnx')
        mini_gauge("🇺🇸 나스닥", data['nas'], 15000, 40000, 'stock', url_key='nas') 
        # 코스피: 최대치 8000 -> 7000 수정
        mini_gauge("🇰🇷 코스피", data['kospi'], 2000, 7000, 'stock', url_key='kospi')
    with c2:
        # WTI 유가: 최대치 100 -> 90 수정
        mini_gauge("🛢️ WTI 유가", data['oil'], 60, 90, 'risk', '$', 'oil')
        mini_gauge("🇺🇸 S&P 500", data['sp5'], 4500, 10000, 'stock', url_key='sp5')
        mini_gauge("🇰🇷 코스닥", data['kosdaq'], 600, 3000, 'stock', url_key='kosdaq') 
    with c3:
        # 환율: 최대치 1550 -> 1500 수정
        mini_gauge("🇰🇷 환율", data['krw'], 1300, 1500, 'risk', '원', 'krw')
        mini_gauge("💾 반도체(SOX)", data['sox'], 3000, 10000, 'stock', url_key='sox') 
        
        k_val = inv['raw_data'].get('kospi_foreigner', '0')
        f_color = "#d32f2f" if inv['kospi_foreigner'] < 0 else "#1565c0" 
        st.markdown(f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; margin-top:5px;">
            <p style="margin:0; font-size:14px; color:#333;">💰 <b>외국인 수급 (코스피)</b></p>
            <p style="margin:5px 0 0 0; font-size:18px; font-weight:bold; color:{f_color};">{k_val}억</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 섹션 2: 대체 자산 & 공포지수
    st.subheader("🛡️ 대체 자산 & 공포지수")
    c7, c8, c9, c10 = st.columns(4)
    # 금: 최대치 10000 -> 8000 수정
    with c7: mini_gauge("🟡 금(Gold)", data['gold'], 2000, 8000, 'stock', '$', 'gold') 
    with c8: mini_gauge("⚪ 은(Silver)", data['silver'], 20, 150, 'stock', '$', 'silver') 
    # 비트코인: 최대치 200000 -> 150000 수정
    with c9: mini_gauge("₿ 비트코인", data['btc'], 0, 150000, 'stock', '$', 'btc') 
    with c10: mini_gauge("😨 VIX(공포)", data['vix'], 10, 50, 'risk', url_key='vix') 

    # --- 위험도 산정 (기준 변경 반영) ---
    def calc_r(v, min_v, max_v): return max(0, min(100, (v - min_v) / (max_v - min_v) * 100))
    # TNX: Max 5.0 (기존과 동일하지만 유지)
    # Oil: Max 100 -> 90으로 위험도 민감도 조정
    # KRW: Max 1550 -> 1500으로 위험도 민감도 조정
    risk_score = int((calc_r(data['tnx']['val'], 3.5, 5.0) + calc_r(data['oil']['val'], 65, 90) + calc_r(data['krw']['val'], 1350, 1500) + calc_r(data['vix']['val'], 15, 35) + calc_r(-data['sox']['pct'], 0, 10) + calc_r(-min(data['kospi']['pct'], data['kosdaq']['pct']), 0, 10) + calc_r(-inv['kospi_foreigner']/10, 0, 500)) / 7)
    
    st.subheader(f"📊 종합 시장 위험도: {risk_score}점")
    
    # --- 보고서 출력 ---
    news_summary = " / ".join([n['title'] for n in news['semi'][:3]])
    calendar_str = "\n".join([f"{c['time']} {c['event']} (★{c['importance']})" for c in calendar])
    
    ai_report = get_ai_portfolio_analysis(st.session_state.api_key, data, inv, risk_score, news_summary, calendar_str)
    
    is_error = False
    error_msg = ""
    if ai_report and "error" in ai_report:
        is_error = True
        error_msg = ai_report['error']
        ai_report = None

    mode_label = "🤖 AI 애널리스트" if ai_report else "⚙️ 기본 분석 엔진"
    if not ai_report: 
        ai_report = get_basic_report(data, inv, risk_score, news, calendar)
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
