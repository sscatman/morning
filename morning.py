import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="시장 정밀 분석 (100점 만점)",
    page_icon="📊",
    layout="wide"
)

# --- 스타일링 (CSS) 수정됨 ---
st.markdown("""
    <style>
    /* 1. 폰트 패밀리 설정 (아이콘 깨짐 방지: * 대신 구체적 태그 지정) */
    html, body, p, h1, h2, h3, h4, div, span, label, li, a {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 2. 헤더 타이틀: 테마에 따라 자동 변환 */
    .header-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 5px;
        /* 색상 지정 삭제 -> 다크모드 자동 대응 */
    }
    .sub-info {
        font-size: 14px;
        opacity: 0.8; /* 색상 대신 투명도 사용 */
    }
    
    /* 3. 가로 스크롤 카드 (배경이 흰색이므로 글씨는 검은색 강제) */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 12px;
        padding-bottom: 10px;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
    }
    .metric-card {
        background-color: #ffffff; /* 흰색 배경 고정 */
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        min-width: 130px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: inline-block;
    }
    .metric-title { font-size: 13px; color: #666 !important; margin-bottom: 5px; }
    .metric-value { font-size: 18px; font-weight: 800; color: #000 !important; } /* 검은색 강제 */
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
        color: #333 !important; /* 배경이 흰색이므로 검은글씨 */
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
        color: #999; /* 기본 회색 */
        font-size: 11px;
        font-weight: bold;
    }
    .scale-mark { position: relative; width: 30px; text-align: center; }
    .scale-mark::before {
        content: ''; position: absolute; top: -8px; left: 50%; width: 1px; height: 6px; background-color: #ccc;
    }

    /* 5. 행동 가이드 박스 (배경이 밝은색이므로 글씨는 검은색 강제) */
    .guide-box {
        padding: 20px;
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        color: #111 !important; /* 내부 텍스트 검은색 강제 */
    }
    .guide-header {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 10px;
        color: #000 !important;
    }
    /* 가이드 박스 내부의 p 태그 등도 검은색 강제 */
    .guide-box p, .guide-box li, .guide-box span, .guide-box div {
        color: #111;
    }
    
    .investor-box {
        margin-top: 15px;
        padding: 12px;
        background-color: #f8f9fa; /* 밝은 회색 배경 */
        border-radius: 8px;
        border: 1px solid #eee;
        font-size: 13px;
        color: #111 !important;
    }
    
    /* 6. 뉴스 리스트 (배경 없음 -> 다크모드 자동 적응) */
    .news-item {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0; /* 다크모드에선 흐리게 보일 수 있음, 투명도 조절 권장 */
        font-size: 14px;
    }
    @media (prefers-color-scheme: dark) {
        .news-item { border-bottom: 1px solid #444; }
    }
    .news-item:last-child { border-bottom: none; }
    
    .news-title { 
        font-weight: 600; 
        /* color: #333 !important; 삭제 -> 테마 따름 */
        display: block; 
        margin-bottom: 2px; 
    }
    /* 뉴스 제목 링크 스타일 */
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

# --- 함수: 수급 정보 (파싱 로직 개선) ---
def get_kr_market_investors():
    # 네이버 금융 투자자별 매매동향
    url = "https://finance.naver.com/sise/sise_trans_style.naver"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.naver.com/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        # cp949 또는 euc-kr 인코딩
        html = response.content.decode('euc-kr', 'replace')
        soup = BeautifulSoup(html, 'html.parser')
        
        # '시간대별' 테이블이 아니라 상단의 '당일 추이' 값을 찾아야 함
        # 보통 class='type2' 테이블의 첫 번째 데이터 행이 당일 누적치임
        table = soup.find('table', class_='type2')
        if not table: return None

        # 행들 추출
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 컬럼이 충분히 있고, 첫 번째 컬럼(시간)에 숫자나 시간이 포함된 경우
            if len(cols) >= 4:
                time_txt = cols[0].text.strip()
                # 시간(09:00~) 또는 장마감(15:30 등) 텍스트가 있는 행 찾기
                if re.search(r'\d{2}:\d{2}', time_txt):
                    # 순서: 시간 | 개인 | 외국인 | 기관
                    personal = cols[1].text.strip()
                    foreigner = cols[2].text.strip()
                    institution = cols[3].text.strip()
                    
                    # 데이터가 비어있지 않으면 반환
                    if personal and foreigner:
                        return {"개인": personal, "외국인": foreigner, "기관": institution}
        return None
    except Exception:
        return None

# --- 함수: 뉴스 크롤링 (연준/국내) ---
def get_financial_news():
    news_data = {"fed": [], "korea": []}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. 국내 주요 뉴스 (네이버 금융 메인)
        url_kr = "https://finance.naver.com/news/mainnews.naver"
        res_kr = requests.get(url_kr, headers=headers, timeout=5)
        soup_kr = BeautifulSoup(res_kr.content.decode('euc-kr', 'replace'), 'html.parser')
        
        # 주요 뉴스 리스트 추출
        articles = soup_kr.select('.block1 a') # 썸네일 제외 텍스트 링크
        count = 0
        for ar in articles:
            title = ar.text.strip()
            link = "https://finance.naver.com" + ar['href']
            if title and count < 5:
                news_data["korea"].append({"title": title, "link": link})
                count += 1

        # 2. 해외/연준 관련 뉴스 (해외증시 섹션)
        url_fed = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258" 
        res_fed = requests.get(url_fed, headers=headers, timeout=5)
        soup_fed = BeautifulSoup(res_fed.content.decode('euc-kr', 'replace'), 'html.parser')
        
        # '연준', 'Fed', '금리', 'FOMC', '파월' 키워드 필터링
        fed_keywords = ['연준', 'Fed', 'FED', '금리', 'FOMC', '파월', '물가', '긴축', '부양']
        
        fed_articles = soup_fed.select('.newsList li dl')
        fed_count = 0
        
        for item in fed_articles:
            # 제목 추출 (dt 안에 a가 있을수도, dd 안에 있을수도 있음)
            subject_tag = item.select_one('.articleSubject a')
            if not subject_tag: continue
            
            title = subject_tag.text.strip()
            link = "https://finance.naver.com" + subject_tag['href']
            summary_tag = item.select_one('.articleSummary')
            summary = summary_tag.text.strip()[:60] + "..." if summary_tag else ""
            
            # 키워드 매칭
            if any(k in title for k in fed_keywords) or any(k in summary for k in fed_keywords):
                if fed_count < 4:
                    news_data["fed"].append({"title": title, "link": link, "summary": summary})
                    fed_count += 1
                    
    except Exception:
        pass
        
    return news_data

# --- 함수: 데이터 가져오기 (주식) ---
def get_all_data():
    tickers = {
        "tnx": "^TNX",   # 미국 10년물 국채
        "oil": "CL=F",   # WTI 유가
        "krw": "KRW=X",  # 원/달러 환율
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
    except Exception as e:
        return None, e

# --- 메인 헤더 ---
weather = get_weather("Daejeon")
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

st.markdown(f"""
<div class="header-title">📊 시장 위험도 분석 </div>
<div class="sub-info">📍 대전: {weather} | 🕒 {now_str} 기준</div>
<hr>
""", unsafe_allow_html=True)

# --- 데이터 로딩 ---
raw_data, error = get_all_data()
investor_data = get_kr_market_investors()
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
        {make_card("📉 코스피", kospi_val, kospi_pct, True)}
        {make_card("📉 코스닥", kosdaq_val, kosdaq_pct, True)}
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)
    st.caption("↔️ 좌우로 스크롤하여 모든 지표를 확인하세요.")
    st.markdown("---")

    # 2. 100점 만점 위험도 계산
    def map_score(value, min_val, max_val, max_score=25):
        if value <= min_val: return 0
        if value >= max_val: return max_score
        return (value - min_val) / (max_val - min_val) * max_score

    total_risk_score = 0
    reasons = []

    # 국채 (3.8~4.5%)
    tnx_score = map_score(tnx_val, 3.80, 4.50, 25)
    total_risk_score += tnx_score
    if tnx_score >= 10: reasons.append(f"국채금리 {tnx_val:.2f}% (위험도 {int(tnx_score)}/25)")

    # 유가 ($75~$90)
    oil_score = map_score(oil_val, 75.0, 90.0, 25)
    total_risk_score += oil_score
    if oil_score >= 10: reasons.append(f"유가 ${oil_val:.2f} (위험도 {int(oil_score)}/25)")

    # 환율 (1350~1450원)
    krw_score = map_score(krw_val, 1350, 1450, 25)
    total_risk_score += krw_score
    if krw_score >= 10: reasons.append(f"환율 {krw_val:.0f}원 (위험도 {int(krw_score)}/25)")

    # 증시 급락 (-0.5% ~ -2.5%)
    market_drop = min(kospi_pct, kosdaq_pct)
    market_score = map_score(-market_drop, 0.5, 2.5, 25)
    total_risk_score += market_score
    if market_score >= 10: reasons.append(f"증시 변동성 {market_drop:.2f}% (위험도 {int(market_score)}/25)")

    final_score = int(total_risk_score)
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

    # 4. 행동 가이드
    guide_msg = ""
    guide_bg = ""
    level_text = ""

    if final_score >= 85:
        level_text = "위험도 [최고조] - 시장 붕괴"
        guide_msg = "공황 상태입니다. 매매 중단, 현금 100%."
        guide_bg = "#ffebee"
    elif final_score >= 70:
        level_text = "위험도 [매우 높음] - 폭락 경보"
        guide_msg = "소나기입니다. 반등 시 현금 확보."
        guide_bg = "#ffebee"
    elif final_score >= 50:
        level_text = "위험도 [높음] - 하락장"
        guide_msg = "보수적 대응. 물타기 금지."
        guide_bg = "#fff3e0"
    elif final_score >= 35:
        level_text = "위험도 [경계] - 관망"
        guide_msg = "신규 진입 자제. 리스크 관리."
        guide_bg = "#fff3e0"
    elif final_score >= 20:
        level_text = "위험도 [주의] - 변동성"
        guide_msg = "분할 매수로 대응하세요."
        guide_bg = "#fffde7"
    elif final_score >= 10:
        level_text = "위험도 [양호] - 투자 적기"
        guide_msg = "실적주 위주로 매수하세요."
        guide_bg = "#f1f8e9"
    else:
        level_text = "위험도 [최상] - 적극 매수"
        guide_msg = "골디락스 구간입니다. 수익 극대화!"
        guide_bg = "#e8f5e9"

    # 수급 정보 HTML
    if investor_data:
        investor_content = f"""
        <span style="color:#d62728; font-weight:bold;">개인: {investor_data['개인']}</span> &nbsp;|&nbsp; 
        <span style="color:#1f77b4; font-weight:bold;">외국인: {investor_data['외국인']}</span> &nbsp;|&nbsp; 
        <span style="color:#2ca02c; font-weight:bold;">기관: {investor_data['기관']}</span>
        """
    else:
        investor_content = "<span style='color:#999;'>수급 정보 로딩 중... (장 시작 전이거나 집계 지연)</span>"

    if reasons:
        reason_items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in reasons])
        reason_content = f"<ul style='margin-top:5px; padding-left:20px; color:#d32f2f; font-weight:600;'>{reason_items}</ul>"
    else:
        reason_content = "<p style='margin-top:5px; color:#2e7d32; font-weight:bold;'>✅ 특이 사항 없음</p>"

    # 가이드 박스 출력
    guide_html = f"""
    <div class="guide-box" style="background-color: {guide_bg};">
        <div class="guide-header">👉 현재 상태: {level_text}</div>
        <p style="font-weight:bold; font-size:16px; margin-bottom:15px;">{guide_msg}</p>
        <div style="border-top: 1px solid rgba(0,0,0,0.1); padding-top:15px;">
            <strong>🚨 주요 위험 요인:</strong>
            {reason_content}
        </div>
        <div class="investor-box">
            <strong style="display:block; margin-bottom:5px;">💰 코스피 수급 (오늘 누적):</strong>
            {investor_content}
        </div>
    </div>
    """
    st.markdown(guide_html, unsafe_allow_html=True)
    
    # --- 5. 추가 정보 섹션 (뉴스) ---
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
        else:
            st.info("연준 관련 최신 주요 뉴스가 없습니다.")
            
    with c2:
        st.markdown("### 🇰🇷 국내 증시 주요 체크")
        if news_data and news_data['korea']:
            for item in news_data['korea']:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("국내 주요 뉴스를 불러오지 못했습니다.")

    st.markdown("---")
    
    with st.expander("📜 100점 만점 기준 가이드라인 보기"):
        st.markdown("""
        | 위험 점수 | 상태 | 행동 요령 |
        |---|---|---|
        | **85~100** | 🌪️ 붕괴 | 현금 100% 확보. |
        | **70~84** | ☔️ 폭락 | 투매 금지. 반등 시 매도. |
        | **50~69** | 🌧️ 하락 | 물타기 금지. 보수적 대응. |
        | **35~49** | ☁️ 경계 | 신규 매수 자제. 현금 확대. |
        | **20~34** | ⛅️ 주의 | 변동성 구간. 분할 매매. |
        | **10~19** | 🌤️ 양호 | 실적주 매수 대응. |
        | **0~9** | ☀️ 최상 | 적극 매수 구간. |
        """)

