import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import json 

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="위험도 분석 (V0.44)", # 버전 업데이트
    page_icon="📊",
    layout="wide"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    /* 1. 폰트 설정 */
    html, body, p, h1, h2, h3, h4, div, span, label, li, a {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 2. 헤더 타이틀 */
    .header-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .sub-info {
        font-size: 14px;
        opacity: 0.8;
    }
    
    /* 3. 개별 지표 게이지 바 스타일 */
    .mini-gauge-container {
        margin-bottom: 15px;
        padding: 10px;
        background-color: #fff;
        border-radius: 8px;
        border: 1px solid #eee;
    }
    .mini-gauge-title {
        font-size: 14px;
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .mini-gauge-track {
        position: relative;
        width: 100%;
        height: 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
        margin-top: 5px;
    }
    .mini-gauge-pointer {
        position: absolute;
        top: -6px;
        width: 12px;
        height: 22px;
        background-color: #333;
        border: 2px solid #fff;
        border-radius: 3px;
        transform: translateX(-50%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .mini-gauge-labels {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: #888;
        margin-top: 3px;
    }
    /* 링크 호버 효과 */
    a.gauge-link:hover {
        color: #2979ff !important;
        text-decoration: underline !important;
    }

    /* 4. 메인 위험도 바 스타일 */
    .risk-wrapper {
        position: relative;
        width: 100%;
        height: 90px;
        margin-top: 30px;
        margin-bottom: 10px;
        padding: 0 10px;
    }
    .risk-track {
        position: absolute;
        top: 45px;
        left: 0;
        width: 100%;
        height: 14px;
        background-color: #eee;
        border-radius: 7px;
        overflow: hidden;
    }
    .risk-fill {
        height: 100%;
        border-radius: 7px;
        background: linear-gradient(90deg, #00e676 0%, #ffeb3b 50%, #ff3d00 100%);
        transition: width 1s;
    }
    .risk-pointer {
        position: absolute;
        top: 0;
        transform: translateX(-50%);
        width: 60px;
        height: 35px;
        background: #fff;
        border-radius: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        text-align: center;
        line-height: 33px;
        font-weight: 800;
        font-size: 14px;
        color: #333 !important;
        border: 2px solid;
        z-index: 10;
        transition: left 1s;
    }
    .risk-pointer::after {
        content: '';
        position: absolute;
        bottom: -6px;
        left: 50%;
        transform: translateX(-50%);
        border-width: 6px 6px 0;
        border-style: solid;
        border-color: inherit transparent transparent transparent;
        display: block;
        width: 0;
    }
    .risk-scale {
        position: absolute;
        top: 65px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: space-between;
        color: #999;
        font-size: 11px;
        font-weight: bold;
    }
    .scale-mark { position: relative; width: 30px; text-align: center; }
    .scale-mark::before {
        content: ''; position: absolute; top: -8px; left: 50%; width: 1px; height: 6px; background-color: #ccc;
    }

    /* 5. 가이드 박스 */
    .guide-box {
        padding: 25px;
        background-color: #ffffff;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        color: #111 !important;
    }
    .guide-header {
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 15px;
        color: #000 !important;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 10px;
    }
    .guide-section-title {
        font-size: 16px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 8px;
        color: #333 !important;
    }
    .guide-text {
        font-size: 15px;
        line-height: 1.6;
        margin-bottom: 10px;
        color: #444 !important;
    }
    /* 다크모드 대응 */
    .guide-box p, .guide-box li, .guide-box span, .guide-box div, .guide-box strong { color: #111 !important; }
    
    .factor-container {
        display: flex;
        gap: 20px;
        margin-top: 20px;
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
    }
    .factor-column { flex: 1; }
    @media (max-width: 768px) {
        .factor-container { flex-direction: column; gap: 15px; }
        .factor-column { border-left: none !important; padding-left: 0 !important; }
    }

    .investor-box {
        margin-top: 15px;
        padding: 12px;
        background-color: #e3f2fd;
        border-radius: 8px;
        font-size: 14px;
        color: #1565c0 !important;
        font-weight: bold;
        text-align: center;
    }
    
    /* 6. 뉴스 리스트 */
    .news-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 14px;
    }
    @media (prefers-color-scheme: dark) {
        .news-item { border-bottom: 1px solid #444; }
    }
    .news-item:last-child { border-bottom: none; }
    
    .news-title { font-weight: 600; display: block; margin-bottom: 2px; }
    a.news-title:hover { text-decoration: underline; color: #2979ff !important; }
    .news-meta { font-size: 12px; opacity: 0.7; }
    .fed-badge { 
        background-color: #e3f2fd; color: #1565c0 !important; 
        padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바: 설정 ---
with st.sidebar:
    st.header("⚙️ 설정")
    gemini_api_key = st.text_input("🔑 Gemini API 키", type="password", placeholder="API Key 입력 시 AI 분석 활성화").strip() # 공백 제거
    if st.button('🔄 데이터 새로고침'):
        st.rerun()
    st.info("API 키가 없으면 기본 분석이 제공됩니다.")

# --- 함수: 날씨 ---
def get_weather(city="Daejeon"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t&_={int(time.time())}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200: return response.text.strip()
        return "N/A"
    except: return "N/A"

# --- 함수: 수급 정보 ---
def get_market_investors():
    url = "https://finance.naver.com/"
    headers = { 'User-Agent': 'Mozilla/5.0' }
    result = { "kospi_foreigner": 0, "kospi_institution": 0, "kosdaq_foreigner": 0, "futures_foreigner": 0, "raw_data": {} }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        html = response.content.decode('euc-kr', 'replace')
        soup = BeautifulSoup(html, 'html.parser')
        
        def parse_amount(text):
            try: return int(re.sub(r'[^\d\-]', '', text)) if re.sub(r'[^\d\-]', '', text) else 0
            except: return 0

        investor_tables = soup.select('.tbl_home')
        for tbl in investor_tables:
            if "외국인" in tbl.text and "기관" in tbl.text:
                rows = tbl.select('tr')
                for row in rows:
                    cols = row.select('td')
                    if not cols: continue
                    label = row.select_one('th').text.strip() if row.select_one('th') else ""
                    
                    if "거래소" in label or "코스피" in label:
                        if len(cols) >= 2:
                            result["kospi_foreigner"] = parse_amount(cols[1].text)
                            result["raw_data"]["kospi_foreigner"] = cols[1].text.strip()
                            result["kospi_institution"] = parse_amount(cols[2].text)
                    elif "코스닥" in label:
                        if len(cols) >= 2:
                            result["kosdaq_foreigner"] = parse_amount(cols[1].text)
                            result["raw_data"]["kosdaq_foreigner"] = cols[1].text.strip()
                    elif "선물" in label:
                        if len(cols) >= 2:
                            result["futures_foreigner"] = parse_amount(cols[1].text)
                            result["raw_data"]["futures_foreigner"] = cols[1].text.strip()
        return result
    except: return None

# --- 함수: 뉴스 크롤링 ---
def get_financial_news():
    news_data = {"us_tech": [], "korea_semi": []}
    headers = {'User-Agent': 'Mozilla/5.0'}
    keywords_us = ['나스닥', 'S&P', '엔비디아', '테슬라', '애플', '마이크론', 'TSMC', '반도체', 'AI', '뉴욕증시', '미증시', 'VIX']
    keywords_kr_semi = ['삼성전자', 'SK하이닉스', '하이닉스', '반도체', 'HBM', '삼전', '소부장']
    
    try:
        url_kr = "https://finance.naver.com/news/mainnews.naver"
        res_kr = requests.get(url_kr, headers=headers, timeout=5)
        soup_kr = BeautifulSoup(res_kr.content.decode('euc-kr', 'replace'), 'html.parser')
        articles = soup_kr.select('.block1 a')
        count = 0
        for ar in articles:
            title = ar.text.strip()
            link = "https://finance.naver.com" + ar['href']
            is_semi = any(k in title for k in keywords_kr_semi)
            if count < 5:
                display_title = f"💾 {title}" if is_semi else title
                news_data["korea_semi"].append({"title": display_title, "link": link})
                count += 1

        url_fed = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258" 
        res_fed = requests.get(url_fed, headers=headers, timeout=5)
        soup_fed = BeautifulSoup(res_fed.content.decode('euc-kr', 'replace'), 'html.parser')
        fed_articles = soup_fed.select('.newsList li dl')
        us_count = 0
        for item in fed_articles:
            subject_tag = item.select_one('.articleSubject a')
            if not subject_tag: continue
            title = subject_tag.text.strip()
            link = "https://finance.naver.com" + subject_tag['href']
            summary_tag = item.select_one('.articleSummary')
            summary = summary_tag.text.strip()[:60] + "..." if summary_tag else ""
            if any(k in title for k in keywords_us) or any(k in summary for k in keywords_us):
                if us_count < 5:
                    news_data["us_tech"].append({"title": title, "link": link, "summary": summary})
                    us_count += 1
    except: pass
    return news_data

# --- [수정] 함수: 제미나이 AI 브리핑 생성 (에러 핸들링 강화) ---
def get_gemini_briefing(api_key, market_data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    당신은 전문 주식 애널리스트입니다. 아래 시장 데이터를 바탕으로 한국 투자자를 위한 '시장 분석 보고서'를 작성해주세요.
    
    [시장 데이터]
    - 미국채 10년: {market_data['tnx']:.2f}%
    - WTI 유가: ${market_data['oil']:.2f}
    - 원/달러 환율: {market_data['krw']:.0f}원
    - 필라델피아 반도체: {market_data['sox']:.2f}% (등락률)
    - 나스닥: {market_data['nas']:.2f}% (등락률)
    - 코스피: {market_data['kospi']:.2f}% (등락률)
    - 외국인 수급: 현물 {market_data['buy']}억 / 선물 {market_data['fut']}억
    - VIX 지수: {market_data['vix']:.2f}
    - 종합 위험도 점수: {market_data['score']}점 (100점 만점, 높을수록 위험)

    [요청 사항]
    1. '핵심 요약'은 현재 시장의 가장 큰 특징 1가지를 명확하게 한 문장으로 요약하세요. (이모지 사용)
    2. '투자 판단'은 매수/관망/매도 중 하나의 포지션을 제안하고 그 이유를 한 문장으로 설명하세요.
    3. 말투는 정중하고 전문적으로 작성하세요.
    4. 응답은 반드시 다음 JSON 형식으로만 출력하세요:
    {{
        "summary": "핵심 요약 내용",
        "action": "투자 판단 내용"
    }}
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            text_res = result['candidates'][0]['content']['parts'][0]['text']
            
            # [강화] 정규표현식으로 JSON 객체만 추출 (사족 제거)
            match = re.search(r'\{.*\}', text_res, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return {"error": "AI 응답 파싱 실패"}
        else:
            return {"error": f"API 호출 오류: {response.status_code} ({response.text[:50]}...)"}
    except Exception as e:
        return {"error": f"시스템 오류: {str(e)}"}

# --- 함수: 데이터 가져오기 ---
def get_all_data():
    tickers = {
        "tnx": "^TNX", "oil": "CL=F", "krw": "KRW=X",
        "sox": "^SOX", "sp500": "^GSPC", "nasdaq": "^IXIC",
        "kospi": "^KS11", "kosdaq": "^KQ11",
        "gold": "GC=F", "silver": "SI=F", "btc": "BTC-USD", "vix": "^VIX"
    }
    data = {}
    try:
        for key, symbol in tickers.items():
            df = yf.download(symbol, period="5d", progress=False)
            if len(df) < 2:
                if len(df) == 1: df = pd.concat([df, df])
            data[key] = df
        return data, None
    except Exception as e: return None, e

# --- 메인 헤더 ---
weather = get_weather("Daejeon")
kst_now = datetime.utcnow() + timedelta(hours=9)
now_str = kst_now.strftime('%Y-%m-%d %H:%M')

st.markdown(f"""
<div class="header-title">📊 위험도 분석 (V0.44)</div>
<div class="sub-info">📍 대전: {weather} | 🕒 {now_str} (KST)</div>
<hr>
""", unsafe_allow_html=True)

# --- 데이터 로딩 ---
raw_data, error = get_all_data()
investor_data = get_market_investors()
news_data = get_financial_news()

if error:
    st.error(f"데이터 로딩 실패: {error}")
else:
    def get_info(df):
        if df is None or df.empty: return 0, 0, 0
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        if isinstance(curr, pd.Series): curr = curr.item()
        if isinstance(prev, pd.Series): prev = prev.item()
        diff = curr - prev
        pct = (diff / prev) * 100
        return curr, diff, pct

    # 데이터 추출
    tnx_val, tnx_diff, tnx_pct = get_info(raw_data['tnx'])
    oil_val, oil_diff, oil_pct = get_info(raw_data['oil'])
    krw_val, krw_diff, krw_pct = get_info(raw_data['krw'])
    sox_val, sox_diff, sox_pct = get_info(raw_data['sox'])
    sp5_val, sp5_diff, sp5_pct = get_info(raw_data['sp500'])
    nas_val, nas_diff, nas_pct = get_info(raw_data['nasdaq'])
    kospi_val, kospi_diff, kospi_pct = get_info(raw_data['kospi'])
    kosdaq_val, kosdaq_diff, kosdaq_pct = get_info(raw_data['kosdaq'])
    gold_val, gold_diff, gold_pct = get_info(raw_data['gold'])
    sil_val, sil_diff, sil_pct = get_info(raw_data['silver'])
    btc_val, btc_diff, btc_pct = get_info(raw_data['btc'])
    vix_val, vix_diff, vix_pct = get_info(raw_data['vix'])

    # --- 게이지 바 함수 ---
    def draw_mini_gauge(title, value, display_text, min_val, max_val, color_mode='risk', url=None):
        pct = (value - min_val) / (max_val - min_val) * 100
        pct = max(0, min(pct, 100))
        
        if color_mode == 'risk': bg_gradient = "linear-gradient(90deg, #4CAF50 0%, #FFEB3B 50%, #F44336 100%)"
        elif color_mode == 'stock': bg_gradient = "linear-gradient(90deg, #2196F3 0%, #EEEEEE 50%, #F44336 100%)"
        else: bg_gradient = "linear-gradient(90deg, #E0E0E0 0%, #FFD54F 50%, #FFB300 100%)"
            
        if url: title_html = f'<a href="{url}" target="_blank" class="gauge-link" style="text-decoration:none; color:#333; cursor:pointer;" title="차트 보기">{title} <span style="font-size:0.8em;">🔗</span></a>'
        else: title_html = title
            
        return f"""<div class="mini-gauge-container"><div class="mini-gauge-title"><span>{title_html}</span><span>{display_text}</span></div><div class="mini-gauge-track" style="background: {bg_gradient};"><div class="mini-gauge-pointer" style="left: {pct}%;"></div></div><div class="mini-gauge-labels"><span>{min_val}</span><span>{max_val}</span></div></div>"""

    chart_urls = {
        "tnx": "https://finance.yahoo.com/quote/%5ETNX", "oil": "https://finance.yahoo.com/quote/CL=F",
        "krw": "https://finance.yahoo.com/quote/KRW=X", "nas": "https://finance.yahoo.com/quote/%5EIXIC",
        "sp5": "https://finance.yahoo.com/quote/%5EGSPC", "sox": "https://finance.yahoo.com/quote/%5ESOX",
        "kospi": "https://finance.yahoo.com/quote/%5EKS11", "kosdaq": "https://finance.yahoo.com/quote/%5EKQ11",
        "gold": "https://finance.yahoo.com/quote/GC=F", "silver": "https://finance.yahoo.com/quote/SI=F",
        "btc": "https://finance.yahoo.com/quote/BTC-USD", "vix": "https://finance.yahoo.com/quote/%5EVIX"
    }
    
    st.subheader("📋 주요 지표 상세 현황")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(draw_mini_gauge("🇺🇸 국채 10년 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", tnx_val, f"{tnx_val:.2f}% ({tnx_diff:+.2f})", 3.0, 5.5, 'risk', url=chart_urls['tnx']), unsafe_allow_html=True)
    with c2: st.markdown(draw_mini_gauge("🛢️ WTI 유가 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", oil_val, f"${oil_val:.2f} ({oil_diff:+.2f})", 60.0, 100.0, 'risk', url=chart_urls['oil']), unsafe_allow_html=True)
    with c3: st.markdown(draw_mini_gauge("🇰🇷 환율 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", krw_val, f"{krw_val:.0f}원 ({krw_diff:+.0f})", 1300, 1600, 'risk', url=chart_urls['krw']), unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4: st.markdown(draw_mini_gauge("🇺🇸 나스닥 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", nas_pct, f"{nas_val:.2f} ({nas_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['nas']), unsafe_allow_html=True)
    with c5: st.markdown(draw_mini_gauge("🇺🇸 S&P 500 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", sp5_pct, f"{sp5_val:.2f} ({sp5_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['sp5']), unsafe_allow_html=True)
    with c6: st.markdown(draw_mini_gauge("💾 반도체(SOX) <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", sox_pct, f"{sox_val:.2f} ({sox_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['sox']), unsafe_allow_html=True)

    c7, c8, c9 = st.columns(3)
    with c7: st.markdown(draw_mini_gauge("🇰🇷 코스피 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", kospi_pct, f"{kospi_val:.2f} ({kospi_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['kospi']), unsafe_allow_html=True)
    with c8: st.markdown(draw_mini_gauge("🇰🇷 코스닥 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", kosdaq_pct, f"{kosdaq_val:.2f} ({kosdaq_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['kosdaq']), unsafe_allow_html=True)
    with c9: st.empty()

    st.markdown("---")
    st.subheader("🛡️ 대체 자산 & 공포 지수")
    c10, c11, c12, c13 = st.columns(4)
    with c10: st.markdown(draw_mini_gauge("🌕 금(Gold)", gold_val, f"${gold_val:.1f} ({gold_diff:+.1f})", 1800, 2500, 'neutral', url=chart_urls['gold']), unsafe_allow_html=True)
    with c11: st.markdown(draw_mini_gauge("🪙 은(Silver)", sil_val, f"${sil_val:.1f} ({sil_diff:+.1f})", 20, 35, 'neutral', url=chart_urls['silver']), unsafe_allow_html=True)
    with c12: st.markdown(draw_mini_gauge("₿ 비트코인", btc_pct, f"${btc_val:,.0f} ({btc_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['btc']), unsafe_allow_html=True)
    with c13: st.markdown(draw_mini_gauge("😨 VIX (공포) <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", vix_val, f"{vix_val:.2f} ({vix_diff:+.2f})", 10, 40, 'risk', url=chart_urls['vix']), unsafe_allow_html=True)

    st.markdown("---")

    # 2. 종합 위험도 계산
    def calc_score(val, min_risk, max_risk):
        if val <= min_risk: return 0
        if val >= max_risk: return 100
        return (val - min_risk) / (max_risk - min_risk) * 100

    scores, risks, opportunities = [], [], []
    max_single_risk = 0 

    s_tnx = calc_score(tnx_val, 3.50, 5.00)
    scores.append(s_tnx)
    max_single_risk = max(max_single_risk, s_tnx)
    if s_tnx >= 50: risks.append(f"국채금리 부담 ({tnx_val:.2f}%)")
    elif s_tnx < 20: opportunities.append(f"국채금리 안정세 ({tnx_val:.2f}%)")

    s_oil = calc_score(oil_val, 65.0, 100.0)
    scores.append(s_oil)
    max_single_risk = max(max_single_risk, s_oil)
    if s_oil >= 50: risks.append(f"유가 상승 부담 (${oil_val:.2f})")
    elif s_oil < 20: opportunities.append(f"유가 하향 안정 (${oil_val:.2f})")

    s_krw = calc_score(krw_val, 1350, 1550)
    scores.append(s_krw)
    max_single_risk = max(max_single_risk, s_krw)
    if s_krw >= 50: risks.append(f"고환율 지속 ({krw_val:.0f}원)")
    elif s_krw < 20: opportunities.append(f"환율 안정권 ({krw_val:.0f}원)")

    sox_drop = -sox_pct if sox_pct < 0 else 0
    s_sox = calc_score(sox_drop, 1.0, 10.0)
    scores.append(s_sox)
    max_single_risk = max(max_single_risk, s_sox)
    if s_sox >= 50: risks.append(f"반도체 지수 급락 ({sox_pct:.2f}%)")
    elif sox_pct > 1.0: opportunities.append(f"반도체 지수 강세 ({sox_pct:+.2f}%)")

    market_drop = -min(kospi_pct, kosdaq_pct) if min(kospi_pct, kosdaq_pct) < 0 else 0
    s_mkt = calc_score(market_drop, 3.0, 10.0)
    scores.append(s_mkt * 0.1) 
    max_single_risk = max(max_single_risk, s_mkt) 
    if s_mkt > 0: risks.append(f"국내 증시 폭락 ({min(kospi_pct, kosdaq_pct):.2f}%)")
    elif kospi_pct > 0.5: opportunities.append(f"코스피 상승세 ({kospi_pct:+.2f}%)")

    s_supply, s_futures = 0, 0
    net_buy, fut_net_buy = 0, 0
    if investor_data:
        net_buy = investor_data['kospi_foreigner']
        if net_buy < -1000:
            s_supply = calc_score(abs(net_buy), 0, 5000)
            if s_supply >= 40: risks.append(f"외국인 현물 매도 ({net_buy}억)")
        elif net_buy > 1000: opportunities.append(f"외국인 현물 순매수 (+{net_buy}억)")
        
        fut_net_buy = investor_data['futures_foreigner']
        if fut_net_buy < -2000:
            s_futures = calc_score(abs(fut_net_buy), 0, 10000)
            if s_futures >= 40: risks.append(f"외국인 선물 매도 ({fut_net_buy}억)")
        elif fut_net_buy > 2000: opportunities.append(f"외국인 선물 순매수 (+{fut_net_buy}억)")
        scores.append(s_supply)
        scores.append(s_futures)
    else: 
        scores.append(0)
        scores.append(0)

    s_vix = calc_score(vix_val, 15.0, 35.0)
    scores.append(s_vix)
    max_single_risk = max(max_single_risk, s_vix)
    if s_vix >= 50: risks.append(f"공포심리 확산 (VIX {vix_val:.2f})")
    elif vix_val < 15: opportunities.append(f"투자심리 안정 (VIX {vix_val:.2f})")

    if nas_pct < -1.5: risks.append(f"나스닥 하락세 ({nas_pct:.2f}%)")
    elif nas_pct > 1.0: opportunities.append(f"나스닥 상승세 ({nas_pct:+.2f}%)")

    final_score = int(sum(scores) / len(scores))
    if max_single_risk >= 80: final_score = max(final_score, 60)
    elif max_single_risk >= 60: final_score = max(final_score, 40)
    display_percent = max(min(final_score, 100), 2)

    st.subheader(f"📊 종합 시장 위험도: {final_score}점")
    if final_score >= 80: pointer_color = "#ff3d00"
    elif final_score >= 60: pointer_color = "#ff9100"
    elif final_score >= 40: pointer_color = "#ffc400"
    elif final_score >= 20: pointer_color = "#00e676"
    else: pointer_color = "#2979ff"

    risk_bar_html = f"""<div class="risk-wrapper"><div class="risk-pointer" style="left: {display_percent}%; border-color: {pointer_color}; color: {pointer_color};">{final_score}</div><div class="risk-track"><div class="risk-fill" style="width: {display_percent}%;"></div></div><div class="risk-scale"><span class="scale-mark">0</span><span class="scale-mark">20</span><span class="scale-mark">40</span><span class="scale-mark">60</span><span class="scale-mark">80</span><span class="scale-mark">100</span></div></div>"""
    st.markdown(risk_bar_html, unsafe_allow_html=True)

    # 4. 행동 가이드
    level_text = ""
    summary_text = ""
    action_text = ""
    
    if final_score >= 80: level_text = "Lv.5 위험 [최고조]"
    elif final_score >= 60: level_text = "Lv.4 위험 [높음]"
    elif final_score >= 40: level_text = "Lv.3 위험 [경계]"
    elif final_score >= 20: level_text = "Lv.2 위험 [주의]"
    else: level_text = "Lv.1 위험 [양호]"

    # Gemini AI 브리핑
    ai_result = None
    if gemini_api_key:
        with st.spinner('🤖 AI 애널리스트가 시장을 분석 중입니다...'):
            market_data_for_ai = {
                'tnx': tnx_val, 'oil': oil_val, 'krw': krw_val,
                'sox': sox_pct, 'nas': nas_pct, 'kospi': kospi_pct,
                'buy': net_buy, 'fut': fut_net_buy, 'vix': vix_val, 'score': final_score
            }
            ai_result = get_gemini_briefing(gemini_api_key, market_data_for_ai)

    if ai_result and "error" not in ai_result:
        summary_text = f"🤖 <b>AI 분석:</b> {ai_result.get('summary', '분석 중...')}"
        action_text = f"💡 <b>투자 조언:</b> {ai_result.get('action', '데이터 분석 중...')}"
    else:
        # 에러 발생 시 사용자에게 알림
        if ai_result and "error" in ai_result:
            st.error(f"AI 분석 실패: {ai_result['error']}")
            
        # 기존 로직 (Fallback)
        has_risk = len(risks) > 0
        if final_score >= 40:
            risk_str = ", ".join([r.split('(')[0].strip() for r in risks[:2]]) if risks else "불확실성"
            summary_text = f"🚨 <b>{risk_str}</b> 등이 시장을 압박하고 있습니다."
            action_text = "현금 비중을 늘리고 리스크 관리에 집중하세요."
        else:
            if opportunities:
                opp_str = ", ".join([o.split('(')[0] for o in opportunities[:2]])
                summary_text = f"☀️ <b>{opp_str}</b> 등이 시장 상승을 이끌고 있습니다."
                action_text = "적극 투자 구간입니다. 주도 섹터 비중을 확대하세요."
            else:
                summary_text = "⛅ 큰 악재 없이 시장이 숨 고르기 흐름을 보이고 있습니다."
                action_text = "개별 종목 장세가 예상됩니다. 분할 매수하세요."

    # HTML 리스트 생성
    risk_html = ""
    if risks:
        items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in risks])
        risk_html = f"<ul style='margin-top:5px; padding-left:20px; color:#d32f2f; font-weight:600;'>{items}</ul>"
    else: risk_html = "<p style='margin-top:5px; color:#999; padding-left:5px;'>특이 위험 요인이 없습니다.</p>"

    opp_html = ""
    if opportunities:
        items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in opportunities])
        opp_html = f"<ul style='margin-top:5px; padding-left:20px; color:#2e7d32; font-weight:600;'>{items}</ul>"
    else: opp_html = "<p style='margin-top:5px; color:#999; padding-left:5px;'>뚜렷한 상승 모멘텀이 부족합니다.</p>"

    if investor_data and investor_data.get('kospi_foreigner') != 0:
        raw = investor_data['raw_data']
        k_for = raw.get('kospi_foreigner', '0')
        f_for = raw.get('futures_foreigner', '0')
        investor_content = f"""<div style="display:flex; justify-content:space-between; flex-wrap:wrap;"><span>📉 현물(코스피) 외국인: <b>{k_for}억</b></span><span>📉 선물 외국인: <b>{f_for}억</b></span></div>"""
    else: investor_content = "<span style='color:#999;'>수급 정보 집계 중...</span>"

    guide_html = f"""<div class="guide-box"><div class="guide-header">종합 결과: {level_text}</div><div class="guide-section-title">1. 핵심 요약</div><div class="guide-text">{summary_text}</div><div class="guide-section-title">2. 투자 판단</div><div class="guide-text">{action_text}</div><div class="factor-container"><div class="factor-column"><strong style="color:#d32f2f;">🚨 위험 요인 (Risk):</strong>{risk_html}</div><div class="factor-column" style="border-left: 1px solid rgba(0,0,0,0.1); padding-left: 20px;"><strong style="color:#2e7d32;">✅ 투자 긍정 요인 (Opportunity):</strong>{opp_html}</div></div><div class="investor-box"><strong style="display:block; margin-bottom:5px;">💰 외국인 수급 현황 (추정):</strong>{investor_content}</div></div>"""
    st.markdown(guide_html, unsafe_allow_html=True)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🇺🇸 미국 증시 & 반도체 뉴스")
        if news_data and news_data['us_tech']:
            for item in news_data['us_tech']:
                st.markdown(f"""<div class="news-item"><span class="fed-badge">미국/반도체</span><a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a><div class="news-meta">{item['summary']}</div></div>""", unsafe_allow_html=True)
        else: st.info("관련 주요 뉴스가 없습니다.")
    with c2:
        st.markdown("### 🇰🇷 국내 반도체/증시 주요 뉴스")
        if news_data and news_data['korea_semi']:
            for item in news_data['korea_semi']:
                st.markdown(f"""<div class="news-item"><a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a></div>""", unsafe_allow_html=True)
        else: st.info("국내 주요 뉴스를 불러오지 못했습니다.")

    # --- 5분 자동 새로고침 ---
    time.sleep(300)
    st.rerun()
