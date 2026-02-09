import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="위험도 분석 (V0.35)",
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

# --- 상단: 새로고침 버튼 ---
if st.button('🔄 전체 데이터 새로고침', use_container_width=True):
    st.rerun()

# --- 함수: 날씨 ---
def get_weather(city="Daejeon"):
    try:
        # 캐시 방지를 위한 타임스탬프 추가
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

# --- 함수: 뉴스 크롤링 (반도체/미국증시 중심) ---
def get_financial_news():
    news_data = {"us_tech": [], "korea_semi": []}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 키워드 정의
    keywords_us = ['나스닥', 'S&P', '엔비디아', '테슬라', '애플', '마이크론', 'TSMC', '반도체', 'AI', '뉴욕증시', '미증시']
    keywords_kr_semi = ['삼성전자', 'SK하이닉스', '하이닉스', '반도체', 'HBM', '삼전', '소부장']
    
    try:
        # 1. 국내 뉴스 (반도체 위주 필터링)
        url_kr = "https://finance.naver.com/news/mainnews.naver"
        res_kr = requests.get(url_kr, headers=headers, timeout=5)
        soup_kr = BeautifulSoup(res_kr.content.decode('euc-kr', 'replace'), 'html.parser')
        
        articles = soup_kr.select('.block1 a')
        count = 0
        for ar in articles:
            title = ar.text.strip()
            link = "https://finance.naver.com" + ar['href']
            
            # 반도체 키워드가 있으면 우선 수집, 없으면 일반 뉴스 (최대 5개)
            is_semi = any(k in title for k in keywords_kr_semi)
            if count < 5:
                # 반도체 뉴스면 앞에 이모지 추가해서 강조
                display_title = f"💾 {title}" if is_semi else title
                news_data["korea_semi"].append({"title": display_title, "link": link})
                count += 1

        # 2. 해외 뉴스 (미국 증시/반도체 위주)
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
            
            # 미국 증시/반도체 관련 키워드 매칭
            if any(k in title for k in keywords_us) or any(k in summary for k in keywords_us):
                if us_count < 5:
                    news_data["us_tech"].append({"title": title, "link": link, "summary": summary})
                    us_count += 1
    except: pass
    return news_data

# --- 함수: 데이터 가져오기 (미국 증시 포함) ---
def get_all_data():
    tickers = {
        "tnx": "^TNX",   # 미국 10년물 국채
        "oil": "CL=F",   # WTI 유가
        "krw": "KRW=X",  # 원/달러 환율
        "sox": "^SOX",   # 필라델피아 반도체
        "sp500": "^GSPC", # S&P 500 (추가)
        "nasdaq": "^IXIC", # 나스닥 (추가)
        "kospi": "^KS11", # 코스피
        "kosdaq": "^KQ11" # 코스닥
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
# 한국 시간(KST) 적용: UTC + 9시간
kst_now = datetime.utcnow() + timedelta(hours=9)
now_str = kst_now.strftime('%Y-%m-%d %H:%M')

st.markdown(f"""
<div class="header-title">📊 위험도 분석 (V0.35)</div>
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

    # --- [수정] 개별 지표 게이지 바 생성 함수 (URL 링크 추가) ---
    def draw_mini_gauge(title, value, display_text, min_val, max_val, color_mode='risk', url=None):
        # color_mode: 'risk' (Low=Good, High=Bad), 'stock' (Low=Bad, High=Good)
        
        pct = (value - min_val) / (max_val - min_val) * 100
        pct = max(0, min(pct, 100))
        
        if color_mode == 'risk': # 왼쪽(초록) -> 오른쪽(빨강)
            bg_gradient = "linear-gradient(90deg, #4CAF50 0%, #FFEB3B 50%, #F44336 100%)"
        else: # 주식: 왼쪽(파랑/하락) -> 중앙(회색) -> 오른쪽(빨강/상승)
            bg_gradient = "linear-gradient(90deg, #2196F3 0%, #EEEEEE 50%, #F44336 100%)"
            
        # 제목 HTML 처리 (링크 적용)
        if url:
            title_html = f'<a href="{url}" target="_blank" class="gauge-link" style="text-decoration:none; color:#333; cursor:pointer;" title="차트 보기">{title} <span style="font-size:0.8em;">🔗</span></a>'
        else:
            title_html = title
            
        return f"""
        <div class="mini-gauge-container">
            <div class="mini-gauge-title">
                <span>{title_html}</span>
                <span>{display_text}</span>
            </div>
            <div class="mini-gauge-track" style="background: {bg_gradient};">
                <div class="mini-gauge-pointer" style="left: {pct}%;"></div>
            </div>
            <div class="mini-gauge-labels">
                <span>{min_val}</span>
                <span>{max_val}</span>
            </div>
        </div>
        """

    # --- 1. 개별 지표 게이지 바 (3열 배치 / 요청 순서 반영) ---
    st.subheader("📋 주요 지표 상세 현황")
    
    # URL 딕셔너리 생성
    chart_urls = {
        "tnx": "https://finance.yahoo.com/quote/%5ETNX",
        "oil": "https://finance.yahoo.com/quote/CL=F",
        "krw": "https://finance.yahoo.com/quote/KRW=X",
        "nas": "https://finance.yahoo.com/quote/%5EIXIC",
        "sp5": "https://finance.yahoo.com/quote/%5EGSPC",
        "sox": "https://finance.yahoo.com/quote/%5ESOX",
        "kospi": "https://finance.yahoo.com/quote/%5EKS11",
        "kosdaq": "https://finance.yahoo.com/quote/%5EKQ11"
    }
    
    # 1행: 국채, 유가, 환율 (매크로)
    c1, c2, c3 = st.columns(3)
    with c1:
        # 국채 표시 형식 변경: 값 (변동폭)
        st.markdown(draw_mini_gauge("🇺🇸 국채 10년 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", tnx_val, f"{tnx_val:.2f}% ({tnx_diff:+.2f})", 3.0, 5.5, 'risk', url=chart_urls['tnx']), unsafe_allow_html=True)
    with c2:
        # 유가 표시 형식 변경: 값 (변동폭)
        st.markdown(draw_mini_gauge("🛢️ WTI 유가 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", oil_val, f"${oil_val:.2f} ({oil_diff:+.2f})", 60.0, 100.0, 'risk', url=chart_urls['oil']), unsafe_allow_html=True)
    with c3:
        # 환율 표시 형식 변경: 값 (변동폭)
        st.markdown(draw_mini_gauge("🇰🇷 환율 <span style='font-size:0.8em; color:#666;'>(📉낮을수록 좋음)</span>", krw_val, f"{krw_val:.0f}원 ({krw_diff:+.0f})", 1300, 1600, 'risk', url=chart_urls['krw']), unsafe_allow_html=True)

    # 2행: 나스닥, S&P500, 반도체 (미국) - 범위 -10 ~ 10으로 확장
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(draw_mini_gauge("🇺🇸 나스닥 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", nas_pct, f"{nas_val:.2f} ({nas_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['nas']), unsafe_allow_html=True)
    with c5:
        st.markdown(draw_mini_gauge("🇺🇸 S&P 500 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", sp5_pct, f"{sp5_val:.2f} ({sp5_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['sp5']), unsafe_allow_html=True)
    with c6:
        st.markdown(draw_mini_gauge("💾 반도체(SOX) <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", sox_pct, f"{sox_val:.2f} ({sox_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['sox']), unsafe_allow_html=True)

    # 3행: 코스피, 코스닥 (한국) - 범위 -10 ~ 10으로 확장
    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown(draw_mini_gauge("🇰🇷 코스피 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", kospi_pct, f"{kospi_val:.2f} ({kospi_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['kospi']), unsafe_allow_html=True)
    with c8:
        st.markdown(draw_mini_gauge("🇰🇷 코스닥 <span style='font-size:0.8em; color:#666;'>(📈높을수록 좋음)</span>", kosdaq_pct, f"{kosdaq_val:.2f} ({kosdaq_pct:+.2f}%)", -10.0, 10.0, 'stock', url=chart_urls['kosdaq']), unsafe_allow_html=True)
    with c9:
        st.empty() # 빈칸

    st.markdown("---")

    # 2. 종합 위험도 계산 (9개 항목 평균)
    def calc_score(val, min_risk, max_risk):
        if val <= min_risk: return 0
        if val >= max_risk: return 100
        return (val - min_risk) / (max_risk - min_risk) * 100

    scores = []
    reasons = [] 
    positive_factors = []
    max_single_risk = 0 

    # (1) 국채: 3.5 ~ 5.0
    s_tnx = calc_score(tnx_val, 3.50, 5.00)
    scores.append(s_tnx)
    max_single_risk = max(max_single_risk, s_tnx)
    if s_tnx >= 50: reasons.append(f"국채금리 부담 ({tnx_val:.2f}%)")
    elif s_tnx < 20: positive_factors.append(f"국채금리 안정 ({tnx_val:.2f}%)")

    # (2) 유가: 65 ~ 100
    s_oil = calc_score(oil_val, 65.0, 100.0)
    scores.append(s_oil)
    max_single_risk = max(max_single_risk, s_oil)
    if s_oil >= 50: reasons.append(f"유가 상승세 (${oil_val:.2f})")
    elif s_oil < 20: positive_factors.append(f"유가 안정세 (${oil_val:.2f})")

    # (3) 환율: 1350 ~ 1550
    s_krw = calc_score(krw_val, 1350, 1550)
    scores.append(s_krw)
    max_single_risk = max(max_single_risk, s_krw)
    if s_krw >= 50: reasons.append(f"고환율 지속 ({krw_val:.0f}원)")
    elif s_krw < 20: positive_factors.append(f"환율 안정권 ({krw_val:.0f}원)")

    # (4) 반도체 낙폭: -1% ~ -10% (기준 완화: -10% 폭락해야 만점)
    sox_drop = -sox_pct if sox_pct < 0 else 0
    s_sox = calc_score(sox_drop, 1.0, 10.0)
    scores.append(s_sox)
    max_single_risk = max(max_single_risk, s_sox)
    if s_sox >= 50: reasons.append(f"반도체 지수 급락 ({sox_pct:.2f}%)")
    elif sox_pct > 0: positive_factors.append(f"반도체 지수 상승 (+{sox_pct:.2f}%)")

    # (5) 국내 증시 낙폭: -3.0% ~ -10.0% (기준 완화: -10% 폭락해야 만점)
    market_drop = -min(kospi_pct, kosdaq_pct) if min(kospi_pct, kosdaq_pct) < 0 else 0
    s_mkt = calc_score(market_drop, 3.0, 10.0)
    scores.append(s_mkt * 0.1) 
    max_single_risk = max(max_single_risk, s_mkt) 
    if s_mkt > 0: reasons.append(f"증시 폭락 발생 ({min(kospi_pct, kosdaq_pct):.2f}%)")
    elif kospi_pct > 0: positive_factors.append(f"코스피 상승 (+{kospi_pct:.2f}%)")

    # (6,7) 미국 지수(S&P, 나스닥) 낙폭 (단순 모니터링용, 점수엔 미반영)
    # 필요한 경우 여기에 로직 추가 가능

    # (8,9) 수급
    s_supply, s_futures = 0, 0
    net_buy, fut_net_buy = 0, 0
    if investor_data:
        net_buy = investor_data['kospi_foreigner']
        if net_buy < 0:
            s_supply = calc_score(abs(net_buy), 0, 5000)
            if s_supply >= 50: reasons.append(f"외국인 현물 매도 ({net_buy}억)")
        elif net_buy > 0: positive_factors.append(f"외국인 현물 순매수 (+{net_buy}억)")
        
        fut_net_buy = investor_data['futures_foreigner']
        if fut_net_buy < 0:
            s_futures = calc_score(abs(fut_net_buy), 0, 10000)
            if s_futures >= 50: reasons.append(f"외국인 선물 매도 ({fut_net_buy}억)")
        elif fut_net_buy > 0: positive_factors.append(f"외국인 선물 순매수 (+{fut_net_buy}억)")
        
        scores.append(s_supply)
        scores.append(s_futures)
        max_single_risk = max(max_single_risk, s_supply, s_futures)
    else: 
        scores.append(0)
        scores.append(0)

    final_score = int(sum(scores) / len(scores))
    if max_single_risk >= 80: final_score = max(final_score, 60)
    elif max_single_risk >= 60: final_score = max(final_score, 40)
    display_percent = max(min(final_score, 100), 2)

    # 3. 메인 위험도 바
    st.subheader(f"📊 종합 시장 위험도: {final_score}점")
    
    if final_score >= 80: pointer_color = "#ff3d00"
    elif final_score >= 60: pointer_color = "#ff9100"
    elif final_score >= 40: pointer_color = "#ffc400"
    elif final_score >= 20: pointer_color = "#00e676"
    else: pointer_color = "#2979ff"

    risk_bar_html = f"""<div class="risk-wrapper"><div class="risk-pointer" style="left: {display_percent}%; border-color: {pointer_color}; color: {pointer_color};">{final_score}</div><div class="risk-track"><div class="risk-fill" style="width: {display_percent}%;"></div></div><div class="risk-scale"><span class="scale-mark">0</span><span class="scale-mark">20</span><span class="scale-mark">40</span><span class="scale-mark">60</span><span class="scale-mark">80</span><span class="scale-mark">100</span></div></div>"""
    st.markdown(risk_bar_html, unsafe_allow_html=True)

    # 4. 행동 가이드
    level_text, summary_text, action_text = "", "", ""
    bad_factors, good_factors = [], []
    
    if s_tnx >= 40: bad_factors.append("국채금리 부담")
    if s_krw >= 40: bad_factors.append("고환율")
    if s_oil >= 40: bad_factors.append("유가 상승")
    if s_supply >= 40 or s_futures >= 40: bad_factors.append("외인 매도")
    if s_sox >= 40: bad_factors.append("반도체 약세")
    if nas_pct <= -2.0: bad_factors.append("미국장 하락")
    
    if s_tnx < 20: good_factors.append("금리 안정")
    if s_krw < 20: good_factors.append("환율 안정")
    if sox_pct > 1.0: good_factors.append("반도체 급등")
    if net_buy > 1000 or fut_net_buy > 1000: good_factors.append("외인 매수세")
    
    if final_score >= 60:
        main_cause = ", ".join(bad_factors[:2])
        summary_text = f"🚨 <b>{main_cause}</b> 등이 시장을 강하게 압박하고 있습니다."
        action_text = "주식 비중을 과감히 줄이고 현금을 확보하세요."
    elif final_score >= 40:
        main_cause = ", ".join(bad_factors[:2]) if bad_factors else "대외 불확실성"
        summary_text = f"☁️ <b>{main_cause}</b>으로 인해 시장이 흔들리고 있습니다."
        action_text = "신규 매수는 자제하고 관망하세요."
    elif final_score >= 20:
        if bad_factors and good_factors:
            summary_text = f"⚖️ <b>{bad_factors[0]}</b> 우려와 <b>{good_factors[0]}</b> 기대가 공존하는 혼조세입니다."
        else: summary_text = "⛅ 뚜렷한 방향성 없는 변동성 장세입니다."
        action_text = "조정 시 우량주 위주로 분할 매수하는 전략이 유효합니다."
    else: 
        summary_text = "☀️ 시장이 안정을 찾았으며 투자 심리가 양호합니다."
        action_text = "적극 매수 구간입니다. 주도 섹터 비중을 늘리세요."

    if final_score >= 80: level_text = "Lv.5 [최고조]"
    elif final_score >= 60: level_text = "Lv.4 [높음]"
    elif final_score >= 40: level_text = "Lv.3 [경계]"
    elif final_score >= 20: level_text = "Lv.2 [주의]"
    else: level_text = "Lv.1 [양호]"

    if investor_data and investor_data.get('kospi_foreigner') != 0:
        raw = investor_data['raw_data']
        k_for = raw.get('kospi_foreigner', '0')
        f_for = raw.get('futures_foreigner', '0')
        investor_content = f"""<div style="display:flex; justify-content:space-between; flex-wrap:wrap;"><span>📉 현물(코스피) 외국인: <b>{k_for}억</b></span><span>📉 선물 외국인: <b>{f_for}억</b></span></div>"""
    else: investor_content = "<span style='color:#999;'>수급 정보 집계 중...</span>"

    if reasons:
        reason_items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in reasons])
        reason_content = f"<ul style='margin-top:5px; padding-left:20px; color:#d32f2f; font-weight:600;'>{reason_items}</ul>"
    else: reason_content = "<p style='margin-top:5px; color:#999;'>특이 위험 요인 없음</p>"

    if positive_factors:
        positive_items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in positive_factors])
        positive_content = f"<ul style='margin-top:5px; padding-left:20px; color:#2e7d32; font-weight:600;'>{positive_items}</ul>"
    else: positive_content = "<p style='margin-top:5px; color:#999;'>특이 호재 요인 없음</p>"

    guide_html = f"""<div class="guide-box"><div class="guide-header">종합 결과: {level_text}</div><div class="guide-section-title">1. 핵심 요약</div><div class="guide-text">{summary_text}</div><div class="guide-section-title">2. 투자 판단</div><div class="guide-text">{action_text}</div><div class="factor-container"><div class="factor-column"><strong style="color:#d32f2f;">🚨 위험 요인 (Risk):</strong>{reason_content}</div><div class="factor-column" style="border-left: 1px solid rgba(0,0,0,0.1); padding-left: 20px;"><strong style="color:#2e7d32;">✅ 투자 긍정 요인 (Opportunity):</strong>{positive_content}</div></div><div class="investor-box"><strong style="display:block; margin-bottom:5px;">💰 외국인 수급 현황 (추정):</strong>{investor_content}</div></div>"""
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
