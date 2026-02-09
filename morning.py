import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time  # 자동 갱신을 위한 모듈 추가

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="위험도 분석",
    page_icon="📊",
    layout="wide"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    /* 1. 폰트 패밀리 설정 */
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
    
    /* 3. 가로 스크롤 카드 */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 12px;
        padding-bottom: 10px;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        min-width: 140px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: inline-block;
    }
    .metric-title { font-size: 13px; color: #666 !important; margin-bottom: 5px; }
    .metric-value { font-size: 18px; font-weight: 800; color: #000 !important; }
    .metric-delta { font-size: 12px; font-weight: 600; margin-top: 2px; }
    .plus { color: #d62728 !important; }
    .minus { color: #1f77b4 !important; }

    /* 4. 위험도 바 스타일 */
    .risk-wrapper {
        position: relative;
        width: 100%;
        height: 90px;
        margin-top: 40px;
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
        transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
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
        transition: left 1s cubic-bezier(0.4, 0, 0.2, 1);
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

    /* 5. 행동 가이드 및 정보 박스 */
    .guide-box {
        padding: 20px;
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        color: #111 !important;
    }
    .guide-header {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 10px;
        color: #000 !important;
    }
    .guide-box p, .guide-box li, .guide-box span, .guide-box div { color: #111; }
    
    .investor-box {
        margin-top: 15px;
        padding: 12px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #eee;
        font-size: 13px;
        color: #111 !important;
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
    
    .news-title { 
        font-weight: 600; 
        display: block; 
        margin-bottom: 2px; 
    }
    a.news-title:hover {
        text-decoration: underline;
        color: #2979ff !important;
    }
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
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return response.text.strip()
        return "N/A"
    except:
        return "N/A"

# --- 함수: 수급 정보 ---
def get_market_investors():
    url = "https://finance.naver.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    result = {
        "kospi_foreigner": 0, "kospi_institution": 0,
        "kosdaq_foreigner": 0,
        "futures_foreigner": 0,
        "raw_data": {}
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        html = response.content.decode('euc-kr', 'replace')
        soup = BeautifulSoup(html, 'html.parser')
        
        def parse_amount(text):
            try:
                clean_text = re.sub(r'[^\d\-]', '', text)
                return int(clean_text) if clean_text else 0
            except: return 0

        investor_tables = soup.select('.tbl_home')
        for tbl in investor_tables:
            if "외국인" in tbl.text and "기관" in tbl.text:
                rows = tbl.select('tr')
                for row in rows:
                    th = row.select_one('th')
                    if not th: continue
                    label = th.text.strip()
                    cols = row.select('td')
                    
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
    except Exception: return None

# --- 함수: 뉴스 크롤링 ---
def get_financial_news():
    news_data = {"fed": [], "korea": []}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url_kr = "https://finance.naver.com/news/mainnews.naver"
        res_kr = requests.get(url_kr, headers=headers, timeout=5)
        soup_kr = BeautifulSoup(res_kr.content.decode('euc-kr', 'replace'), 'html.parser')
        
        articles = soup_kr.select('.block1 a')
        count = 0
        for ar in articles:
            title = ar.text.strip()
            link = "https://finance.naver.com" + ar['href']
            if title and count < 4:
                news_data["korea"].append({"title": title, "link": link})
                count += 1

        url_fed = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258" 
        res_fed = requests.get(url_fed, headers=headers, timeout=5)
        soup_fed = BeautifulSoup(res_fed.content.decode('euc-kr', 'replace'), 'html.parser')
        
        fed_keywords = ['연준', 'Fed', 'FED', '금리', 'FOMC', '파월', '물가', '긴축', '부양', '엔비디아', '반도체']
        fed_articles = soup_fed.select('.newsList li dl')
        fed_count = 0
        for item in fed_articles:
            subject_tag = item.select_one('.articleSubject a')
            if not subject_tag: continue
            title = subject_tag.text.strip()
            link = "https://finance.naver.com" + subject_tag['href']
            summary_tag = item.select_one('.articleSummary')
            summary = summary_tag.text.strip()[:60] + "..." if summary_tag else ""
            if any(k in title for k in fed_keywords) or any(k in summary for k in fed_keywords):
                if fed_count < 4:
                    news_data["fed"].append({"title": title, "link": link, "summary": summary})
                    fed_count += 1
    except: pass
    return news_data

# --- 함수: 데이터 가져오기 ---
def get_all_data():
    tickers = {
        "tnx": "^TNX",   # 미국 10년물 국채
        "oil": "CL=F",   # WTI 유가
        "krw": "KRW=X",  # 원/달러 환율
        "sox": "^SOX",   # 필라델피아 반도체
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
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

st.markdown(f"""
<div class="header-title">📊 위험도 분석</div>
<div class="sub-info">📍 대전: {weather} | 🕒 {now_str} 기준</div>
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

    tnx_val, tnx_diff, tnx_pct = get_info(raw_data['tnx'])
    oil_val, oil_diff, oil_pct = get_info(raw_data['oil'])
    krw_val, krw_diff, krw_pct = get_info(raw_data['krw'])
    sox_val, sox_diff, sox_pct = get_info(raw_data['sox'])
    kospi_val, kospi_diff, kospi_pct = get_info(raw_data['kospi'])
    kosdaq_val, kosdaq_diff, kosdaq_pct = get_info(raw_data['kosdaq'])

    # 1. 가로 스크롤 카드
    def make_card(title, value, diff, is_percent=False):
        color_class = "plus" if diff >= 0 else "minus"
        sign = "+" if diff >= 0 else ""
        fmt_val = f"{value:.2f}%" if is_percent else f"{value:.2f}"
        if title == "🇰🇷 환율": fmt_val = f"{value:.0f}원"
        elif title == "🛢️ 유가": fmt_val = f"${value:.2f}"
        
        return f'<div class="metric-card"><div class="metric-title">{title}</div><div class="metric-value">{fmt_val}</div><div class="metric-delta {color_class}">{sign}{diff:.2f}</div></div>'

    cards_html = f"""
    <div class="scroll-container">
        {make_card("🇺🇸 미국채 10년", tnx_val, tnx_diff, True)}
        {make_card("🛢️ 유가", oil_val, oil_diff)}
        {make_card("🇰🇷 환율", krw_val, krw_diff)}
        {make_card("💾 반도체(SOX)", sox_val, sox_pct, True)}
        {make_card("📉 코스피", kospi_val, kospi_pct, True)}
        {make_card("📉 코스닥", kosdaq_val, kosdaq_pct, True)}
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)
    st.caption("↔️ 좌우로 스크롤하여 모든 지표를 확인하세요.")
    st.markdown("---")

    # 2. 종합 위험도 계산 (7개 항목 -> 평균 100점)
    def calc_score(val, min_risk, max_risk):
        if val <= min_risk: return 0
        if val >= max_risk: return 100
        return (val - min_risk) / (max_risk - min_risk) * 100

    scores = []
    reasons = []
    
    # 단독 위험 발생 시 경고 격상을 위한 변수
    max_single_risk = 0 

    # (1) 국채 금리: 3.5% ~ 5.0%
    s_tnx = calc_score(tnx_val, 3.50, 5.00)
    scores.append(s_tnx)
    max_single_risk = max(max_single_risk, s_tnx)
    if s_tnx >= 50: reasons.append(f"국채금리 부담 ({tnx_val:.2f}%)")

    # (2) 유가: $65 ~ $100
    s_oil = calc_score(oil_val, 65.0, 100.0)
    scores.append(s_oil)
    max_single_risk = max(max_single_risk, s_oil)
    if s_oil >= 50: reasons.append(f"유가 상승세 (${oil_val:.2f})")

    # (3) 환율: 1350원 ~ 1550원
    s_krw = calc_score(krw_val, 1350, 1550)
    scores.append(s_krw)
    max_single_risk = max(max_single_risk, s_krw)
    if s_krw >= 50: reasons.append(f"고환율 지속 ({krw_val:.0f}원)")

    # (4) 반도체(SOX) 낙폭: -1% ~ -5%
    sox_drop = -sox_pct if sox_pct < 0 else 0
    s_sox = calc_score(sox_drop, 1.0, 5.0)
    scores.append(s_sox)
    max_single_risk = max(max_single_risk, s_sox)
    if s_sox >= 50: reasons.append(f"반도체 지수 급락 ({sox_pct:.2f}%)")

    # (5) 국내 증시 낙폭: -3.0% ~ -5.0% (가중치 1/10 적용)
    market_drop = -min(kospi_pct, kosdaq_pct) if min(kospi_pct, kosdaq_pct) < 0 else 0
    s_mkt = calc_score(market_drop, 3.0, 5.0)
    scores.append(s_mkt * 0.1) # 평균 점수에는 조금만 반영
    # 단, 단독 위험 판단 시에는 원래 점수 고려 (폭락 시 강제 경고용)
    max_single_risk = max(max_single_risk, s_mkt) 
    if s_mkt > 0: reasons.append(f"증시 폭락 발생 ({min(kospi_pct, kosdaq_pct):.2f}%)")

    # (6) 현물 수급: 5000억 매도 기준
    s_supply = 0
    if investor_data:
        net_buy = investor_data['kospi_foreigner']
        if net_buy < 0:
            s_supply = calc_score(abs(net_buy), 0, 5000)
        scores.append(s_supply)
        max_single_risk = max(max_single_risk, s_supply)
        if s_supply >= 50: reasons.append(f"외국인 현물 매도 ({net_buy}억)")
    else: scores.append(0)

    # (7) 선물 수급: 1조원 매도 기준
    s_futures = 0
    if investor_data:
        fut_net_buy = investor_data['futures_foreigner']
        if fut_net_buy < 0:
            s_futures = calc_score(abs(fut_net_buy), 0, 10000)
        scores.append(s_futures)
        max_single_risk = max(max_single_risk, s_futures)
        if s_futures >= 50: reasons.append(f"외국인 선물 매도 ({fut_net_buy}억)")
    else: scores.append(0)

    # 평균 점수 산출
    final_score = int(sum(scores) / len(scores))
    
    # [중요 수정] 평균은 낮아도, 단독 위험이 높으면 최소 '주의' 이상으로 보정
    # 예: 환율만 1550원이고 나머지가 정상이면 평균은 낮지만, 위험도는 높여야 함
    if max_single_risk >= 80:
        final_score = max(final_score, 60) # 최소 '높음' 단계
    elif max_single_risk >= 60:
        final_score = max(final_score, 40) # 최소 '경계' 단계

    display_percent = max(min(final_score, 100), 2)

    # 3. 위험도 바 렌더링
    st.subheader(f"📊 시장 위험도: {final_score}점")
    
    if final_score >= 80: pointer_color = "#ff3d00"
    elif final_score >= 60: pointer_color = "#ff9100"
    elif final_score >= 40: pointer_color = "#ffc400"
    elif final_score >= 20: pointer_color = "#00e676"
    else: pointer_color = "#2979ff"

    risk_bar_html = f"""
    <div class="risk-wrapper">
        <div class="risk-pointer" style="left: {display_percent}%; border-color: {pointer_color}; color: {pointer_color};">
            {final_score}
        </div>
        <div class="risk-track">
            <div class="risk-fill" style="width: {display_percent}%;"></div>
        </div>
        <div class="risk-scale">
            <span class="scale-mark">0</span>
            <span class="scale-mark">20</span>
            <span class="scale-mark">40</span>
            <span class="scale-mark">60</span>
            <span class="scale-mark">80</span>
            <span class="scale-mark">100</span>
        </div>
    </div>
    """
    st.markdown(risk_bar_html, unsafe_allow_html=True)

    # 4. 행동 가이드 (민감도 조정됨: 기준 점수 하향)
    guide_msg = ""
    guide_bg = ""
    level_text = ""

    if final_score >= 80:
        level_text = "위험도 [최고조] - 시장 붕괴"
        guide_msg = "공황 상태입니다. 매매 중단, 현금 100%."
        guide_bg = "#ffebee"
    elif final_score >= 60:
        level_text = "위험도 [높음] - 하락장"
        guide_msg = "보수적 대응. 현금 비중 확대 필요."
        guide_bg = "#ffebee"
    elif final_score >= 40:
        level_text = "위험도 [경계] - 관망"
        guide_msg = "신규 진입 자제. 리스크 관리 집중."
        guide_bg = "#fff3e0"
    elif final_score >= 20: # 기존 20은 너무 낮았음 -> 적절 (하지만 평균 희석 감안)
        level_text = "위험도 [주의] - 변동성"
        guide_msg = "분할 매수로 대응하세요."
        guide_bg = "#fffde7"
    elif final_score >= 10: # 10점만 넘어도 '양호'로 (기존 0~19가 안전이었음)
        level_text = "위험도 [양호] - 투자 적기"
        guide_msg = "시장이 안정적입니다. 적극 투자 구간."
        guide_bg = "#e8f5e9"
    else:
        level_text = "위험도 [최상] - 적극 매수"
        guide_msg = "골디락스 구간입니다. 수익 극대화!"
        guide_bg = "#e8f5e9"

    if investor_data and investor_data.get('kospi_foreigner') != 0:
        raw = investor_data['raw_data']
        k_for = raw.get('kospi_foreigner', '0')
        f_for = raw.get('futures_foreigner', '0')
        investor_content = f"""
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
            <span>📉 현물(코스피) 외국인: <b>{k_for}억</b></span>
            <span>📉 선물 외국인: <b>{f_for}억</b></span>
        </div>
        """
    else:
        investor_content = "<span style='color:#999;'>수급 정보 집계 중... (장 시작 전이거나 데이터 없음)</span>"

    if reasons:
        reason_items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in reasons])
        reason_content = f"<ul style='margin-top:5px; padding-left:20px; color:#d32f2f; font-weight:600;'>{reason_items}</ul>"
    else:
        reason_content = "<p style='margin-top:5px; color:#2e7d32; font-weight:bold;'>✅ 특이 사항 없음</p>"

    guide_html = f"""
    <div class="guide-box" style="background-color: {guide_bg};">
        <div class="guide-header">👉 현재 상태: {level_text}</div>
        <p style="font-weight:bold; font-size:16px; margin-bottom:15px;">{guide_msg}</p>
        <div style="border-top: 1px solid rgba(0,0,0,0.1); padding-top:15px;">
            <strong>🚨 위험 요인 (항목별 감점):</strong>
            {reason_content}
        </div>
        <div class="investor-box">
            <strong style="display:block; margin-bottom:5px;">💰 외국인 수급 현황 (추정):</strong>
            {investor_content}
        </div>
    </div>
    """
    st.markdown(guide_html, unsafe_allow_html=True)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🇺🇸 연준(Fed) & 글로벌 브리핑")
        if news_data and news_data['fed']:
            for item in news_data['fed']:
                st.markdown(f"""
                <div class="news-item">
                    <span class="fed-badge">Fed/금리</span>
                    <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                    <div class="news-meta">{item['summary']}</div>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("관련 주요 뉴스가 없습니다.")
    with c2:
        st.markdown("### 🇰🇷 국내 증시 주요 체크")
        if news_data and news_data['korea']:
            for item in news_data['korea']:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("국내 주요 뉴스를 불러오지 못했습니다.")

    st.markdown("---")
    with st.expander("📜 위험도 산정 기준 (종합 평균 + 단독 위험 보정)"):
        st.markdown("""
        **총 7개 항목의 평균 점수를 기반으로 하되, 단 하나의 항목이라도 치명적이면 경고 단계를 격상합니다.**
        1. **국채금리:** 3.5% 이상 시 위험 증가 (5.0% 만점)
        2. **유가:** $65 이상 시 위험 증가 ($100 만점)
        3. **환율:** 1,350원 이상 시 위험 증가 (1,550원 만점)
        4. **반도체(SOX):** 전일 대비 하락 시 위험 증가 (-5% 만점)
        5. **국내증시:** -3% 이상 폭락 시 위험 급증 (가중치 0.1배)
        6. **현물 수급:** 외국인 코스피 5천억 매도 만점
        7. **선물 수급:** 외국인 선물 1조원 매도 만점
        """)

    # --- 5분 자동 새로고침 ---
    time.sleep(300)
    st.rerun()
