import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="시장 정밀 분석 (100점 만점)",
    page_icon="📊",
    layout="wide"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    /* 기본 폰트 색상 및 스타일 */
    body, p, h1, h2, h3, h4, div, span, label, li {
        color: #111 !important;
        font-family: 'Pretendard', sans-serif;
    }
    
    .header-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 5px;
        color: #000 !important;
    }
    .sub-info {
        font-size: 14px;
        color: #555 !important;
    }
    
    /* 가로 스크롤 카드 컨테이너 */
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
        min-width: 130px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: inline-block;
    }
    .metric-title { font-size: 13px; color: #666 !important; margin-bottom: 5px; }
    .metric-value { font-size: 18px; font-weight: 800; color: #000 !important; }
    .metric-delta { font-size: 12px; font-weight: 600; margin-top: 2px; }
    .plus { color: #d62728 !important; }
    .minus { color: #1f77b4 !important; }

    /* --- 개선된 위험도 바 (그라데이션 + 포인트) --- */
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
        /* 초록 -> 노랑 -> 빨강 그라데이션 */
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
        color: #333;
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
        color: #999 !important;
        font-size: 11px;
        font-weight: bold;
    }
    .scale-mark {
        position: relative;
        width: 30px;
        text-align: center;
    }
    .scale-mark::before {
        content: '';
        position: absolute;
        top: -8px;
        left: 50%;
        width: 1px;
        height: 6px;
        background-color: #ccc;
    }

    /* 행동 가이드 박스 */
    .guide-box {
        padding: 20px;
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .guide-header {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 10px;
        color: #222 !important;
    }
    .investor-box {
        margin-top: 15px;
        padding: 12px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #eee;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 상단: 새로고침 버튼 ---
if st.button('🔄 데이터 새로고침', use_container_width=True):
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

# --- 함수: 수급 정보 (크롤링 강화) ---
def get_kr_market_investors():
    url = "https://finance.naver.com/sise/sise_trans_style.naver"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://finance.naver.com/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        html = response.content.decode('euc-kr', 'replace')
        soup = BeautifulSoup(html, 'html.parser')
        
        table = soup.find('table', class_='type2')
        if not table: return None

        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 8: 
                personal = cols[1].text.strip()
                foreigner = cols[2].text.strip()
                institution = cols[3].text.strip()
                if personal and foreigner and institution:
                    return {"개인": personal, "외국인": foreigner, "기관": institution}
        return None
    except Exception:
        return None

# --- 함수: 데이터 가져오기 ---
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
<div class="header-title">📊 사장님의 마켓 레이더 (100점 만점)</div>
<div class="sub-info">📍 대전: {weather} | 🕒 {now_str} 기준</div>
<hr>
""", unsafe_allow_html=True)

# --- 데이터 로딩 ---
raw_data, error = get_all_data()
investor_data = get_kr_market_investors()

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

    # HTML 한 줄 처리
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

    # --- [핵심 수정] 100점 만점 정밀 계산 로직 ---
    # 각 지표별 25점 만점 x 4개 항목 = 100점
    # 선형 매핑(Linear Mapping) 함수 사용
    
    def map_score(value, min_val, max_val, max_score=25):
        """값을 범위 내에서 점수로 환산 (0 ~ max_score)"""
        if value <= min_val: return 0
        if value >= max_val: return max_score
        # 선형 보간
        score = (value - min_val) / (max_val - min_val) * max_score
        return score

    total_risk_score = 0
    reasons = []

    # 1. 국채 금리 (25점 만점)
    # 범위: 3.80%(0점) ~ 4.50%(25점)
    tnx_score = map_score(tnx_val, 3.80, 4.50, 25)
    total_risk_score += tnx_score
    
    if tnx_score >= 10: # 중간 이상 위험 시 경고
        reasons.append(f"국채금리 {tnx_val:.2f}% (위험도 {int(tnx_score)}/25)")

    # 2. 유가 (25점 만점)
    # 범위: $75(0점) ~ $90(25점)
    oil_score = map_score(oil_val, 75.0, 90.0, 25)
    total_risk_score += oil_score
    
    if oil_score >= 10:
        reasons.append(f"유가 ${oil_val:.2f} (위험도 {int(oil_score)}/25)")

    # 3. 환율 (25점 만점)
    # 범위: 1350원(0점) ~ 1450원(25점) - 현실화된 기준
    krw_score = map_score(krw_val, 1350, 1450, 25)
    total_risk_score += krw_score
    
    if krw_score >= 10:
        reasons.append(f"환율 {krw_val:.0f}원 (위험도 {int(krw_score)}/25)")

    # 4. 국내 증시 급락 (25점 만점)
    # 범위: -0.5%(0점) ~ -2.5%(25점)
    market_drop = min(kospi_pct, kosdaq_pct) # 하락폭이 큰 것 기준 (음수)
    # 하락폭을 양수로 변환하여 계산 (-2.5%가 더 큰 위험)
    drop_magnitude = -market_drop
    market_score = map_score(drop_magnitude, 0.5, 2.5, 25)
    total_risk_score += market_score
    
    if market_score >= 10:
        reasons.append(f"증시 변동성 {market_drop:.2f}% (위험도 {int(market_score)}/25)")

    # 총점 (0~100)
    final_score = int(total_risk_score)
    # UI 표시용 퍼센트 (최소 2% 보장)
    display_percent = max(min(final_score, 100), 2)

    # --- UI 렌더링 ---
    st.subheader(f"📊 시장 위험도: {final_score}점")
    
    # 색상 결정
    if final_score >= 80: pointer_color = "#ff3d00" # 빨강 (심각)
    elif final_score >= 60: pointer_color = "#ff9100" # 주황 (위험)
    elif final_score >= 40: pointer_color = "#ffc400" # 노랑 (주의)
    elif final_score >= 20: pointer_color = "#00e676" # 연두 (보통)
    else: pointer_color = "#2979ff" # 파랑 (좋음)

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

    # 행동 가이드 내용
    guide_msg = ""
    guide_bg = ""
    level_text = ""

    # 점수대별 가이드 (100점 기준)
    if final_score >= 85:
        level_text = "위험도 [최고조] - 시장 붕괴"
        guide_msg = "공황 상태입니다. 모든 매매를 중단하고 HTS를 끄십시오. 현금이 왕입니다."
        guide_bg = "#ffebee"
    elif final_score >= 70:
        level_text = "위험도 [매우 높음] - 폭락 경보"
        guide_msg = "소나기가 내립니다. 반등 시마다 주식 비중을 줄이고 현금을 확보하세요."
        guide_bg = "#ffebee"
    elif final_score >= 50:
        level_text = "위험도 [높음] - 하락장 진입"
        guide_msg = "보수적 대응이 필요합니다. 물타기는 금물이며, 확실한 종목만 남기세요."
        guide_bg = "#fff3e0"
    elif final_score >= 35:
        level_text = "위험도 [경계] - 관망 필요"
        guide_msg = "시장이 방향을 탐색 중입니다. 신규 진입은 자제하고 리스크 관리에 집중하세요."
        guide_bg = "#fff3e0"
    elif final_score >= 20:
        level_text = "위험도 [주의] - 변동성 확대"
        guide_msg = "나쁘지 않지만 좋지도 않습니다. 분할 매수로 대응하며 시장을 지켜보세요."
        guide_bg = "#fffde7"
    elif final_score >= 10:
        level_text = "위험도 [양호] - 투자 적기"
        guide_msg = "시장이 안정적입니다. 실적주 위주로 매수하기 좋은 시점입니다."
        guide_bg = "#f1f8e9"
    else:
        level_text = "위험도 [매우 좋음] - 적극 매수"
        guide_msg = "골디락스(Goldilocks)입니다. 주식 비중을 최대로 늘려 수익을 극대화하세요!"
        guide_bg = "#e8f5e9"

    # 수급/요인 HTML
    if investor_data:
        investor_content = f"""
        <span style="color:#d62728; font-weight:bold;">개인: {investor_data['개인']}</span> &nbsp;|&nbsp; 
        <span style="color:#1f77b4; font-weight:bold;">외국인: {investor_data['외국인']}</span> &nbsp;|&nbsp; 
        <span style="color:#2ca02c; font-weight:bold;">기관: {investor_data['기관']}</span>
        """
    else:
        investor_content = "<span style='color:#999;'>수급 정보 로딩 실패 (장 시작 전이거나 데이터를 가져올 수 없음)</span>"

    if reasons:
        reason_items = "".join([f"<li style='margin-bottom:4px;'>{r}</li>" for r in reasons])
        reason_content = f"<ul style='margin-top:5px; padding-left:20px; color:#d32f2f; font-weight:600;'>{reason_items}</ul>"
    else:
        reason_content = "<p style='margin-top:5px; color:#2e7d32; font-weight:bold;'>✅ 특이 사항 없음 (안정적)</p>"

    # 최종 가이드 박스
    guide_html = f"""
    <div class="guide-box" style="background-color: {guide_bg};">
        <div class="guide-header">👉 현재 상태: {level_text}</div>
        <p style="font-weight:bold; font-size:16px; margin-bottom:15px;">{guide_msg}</p>
        <div style="border-top: 1px solid rgba(0,0,0,0.1); padding-top:15px;">
            <strong>🚨 주요 요인 (25점 만점 기준):</strong>
            {reason_content}
        </div>
        <div class="investor-box">
            <strong style="display:block; margin-bottom:5px;">💰 코스피 수급 (잠정):</strong>
            {investor_content}
        </div>
    </div>
    """
    st.markdown(guide_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("📜 100점 만점 기준 가이드라인 보기"):
        st.markdown("""
        | 위험 점수 | 상태 | 행동 요령 |
        |---|---|---|
        | **85~100** | 🌪️ 붕괴 | HTS 삭제 권장. 현금 100% 확보. |
        | **70~84** | ☔️ 폭락 | 투매 금지. 반등 시마다 매도. |
        | **50~69** | 🌧️ 하락 | 물타기 금지. 보수적 대응. |
        | **35~49** | ☁️ 경계 | 신규 매수 자제. 현금 비중 확대. |
        | **20~34** | ⛅️ 주의 | 변동성 구간. 분할 매수/매도. |
        | **10~19** | 🌤️ 양호 | 실적주 위주 매수 대응. |
        | **0~9** | ☀️ 최상 | 적극 매수. 불타기 가능 구간. |
        """)
