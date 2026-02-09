import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from datetime import datetime

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="시장 정밀 분석 (20단계)",
    page_icon="📊",
    layout="wide"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    .header-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 5px;
        color: #111;
    }
    .sub-info {
        font-size: 14px;
        color: #555;
    }
    .big-metric {
        font-size: 20px !important;
        font-weight: bold;
    }
    .risk-box {
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 상단: 새로고침 버튼 ---
if st.button('🔄 전체 데이터 새로고침', use_container_width=True):
    st.rerun()

# --- 함수: 날씨 (대전) ---
def get_weather(city="Daejeon"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return response.text.strip()
        return "N/A"
    except:
        return "N/A"

# --- 함수: 네이버 금융 크롤링 (외국인 수급) ---
# 주의: 네이버 페이지 구조 변경 시 수정 필요
def get_kr_market_investors():
    """
    네이버 금융 리서치 페이지 등에서 장중 외국인 순매수 동향을 파악합니다.
    실시간 정확도는 증권사 HTS보다 떨어질 수 있습니다.
    """
    url = "https://finance.naver.com/"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 금융 홈 상단 데이터 (구조가 복잡하여 예외처리 필수)
        # 여기서는 간단히 크롤링이 어렵다면 모의 로직을 사용하거나
        # 실제로는 API가 없으므로 화면에 '정보 확인 필요'로 띄울 수도 있습니다.
        # *이 코드는 데모용으로 크롤링 시도 후 실패 시 None 반환*
        
        # (실제 크롤링 로직은 페이지 구조에 의존적이므로 
        # 안정성을 위해 여기서는 yfinance의 전일 대비 등락률을 기반으로 
        # 외국인 수급을 '추정'하는 방식으로 대체하거나
        # 투자자별 매매동향 페이지를 파싱해야 합니다.)
        
        # 여기서는 보다 안정적인 yfinance 데이터를 메인으로 쓰되,
        # 외국인 수급은 '알 수 없음(HTS 확인 요망)'으로 두지 않고
        # 코스피 지수가 1% 이상 하락하면 '매도세 추정'으로 로직을 짭니다.
        
        # *강력한 크롤링 대신 지수 기반 추정 로직 사용 (웹페이지 차단 방지)*
        return None 
    except:
        return None

# --- 함수: 글로벌/한국 데이터 가져오기 ---
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
                # 데이터 부족 시 처리
                if len(df) == 1:
                    df = pd.concat([df, df])
            data[key] = df
        return data, None
    except Exception as e:
        return None, e

# --- 메인 헤더 ---
weather = get_weather("Daejeon")
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

st.markdown(f'<div class="header-title">📊 사장님의 마켓 레이더 (20단계 정밀분석)</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-info">📍 대전: {weather} | 🕒 {now_str} 기준</div>', unsafe_allow_html=True)
st.markdown("---")

# --- 데이터 로딩 ---
raw_data, error = get_all_data()

if error:
    st.error(f"데이터 로딩 실패: {error}")
else:
    # 데이터 전처리 함수
    def get_info(df):
        if df is None or df.empty: return 0, 0, 0
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        if isinstance(curr, pd.Series): curr = curr.item()
        if isinstance(prev, pd.Series): prev = prev.item()
        diff = curr - prev
        pct = (diff / prev) * 100
        return curr, diff, pct

    # 각 지표 추출
    tnx_val, tnx_diff, tnx_pct = get_info(raw_data['tnx'])
    oil_val, oil_diff, oil_pct = get_info(raw_data['oil'])
    krw_val, krw_diff, krw_pct = get_info(raw_data['krw'])
    kospi_val, kospi_diff, kospi_pct = get_info(raw_data['kospi'])
    kosdaq_val, kosdaq_diff, kosdaq_pct = get_info(raw_data['kosdaq'])

    # --- 5열 레이아웃 (지표 보여주기) ---
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("🇺🇸 국채(10y)", f"{tnx_val:.3f}%", f"{tnx_diff:.3f}")
    with c2:
        st.metric("🛢️ 유가(WTI)", f"${oil_val:.2f}", f"{oil_diff:.2f}")
    with c3:
        st.metric("🇰🇷 환율", f"{krw_val:.0f}원", f"{krw_diff:.1f}")
    with c4:
        st.metric("📉 코스피", f"{kospi_val:.0f}", f"{kospi_pct:.2f}%")
    with c5:
        st.metric("📉 코스닥", f"{kosdaq_val:.0f}", f"{kosdaq_pct:.2f}%")

    st.markdown("---")

    # --- [핵심] 20단계 위험도 계산 로직 ---
    # 총점 0(천국) ~ 20(지옥)
    risk_score = 0
    reasons = []

    # 1. 국채 금리 (최대 4점)
    if tnx_val >= 4.6: risk_score += 4; reasons.append("국채금리 4.6% 돌파 (매우 심각)")
    elif tnx_val >= 4.4: risk_score += 3; reasons.append("국채금리 4.4% 상회")
    elif tnx_val >= 4.2: risk_score += 2; reasons.append("국채금리 4.2% 상회 (주의)")
    elif tnx_val >= 4.0: risk_score += 1

    # 2. 유가 (최대 4점)
    if oil_val >= 90: risk_score += 4; reasons.append("유가 $90 돌파 (오일쇼크 우려)")
    elif oil_val >= 85: risk_score += 3; reasons.append("유가 $85 상회 (인플레)")
    elif oil_val >= 80: risk_score += 2; reasons.append("유가 $80 상회")
    elif oil_val >= 75: risk_score += 1

    # 3. 환율 (최대 4점)
    if krw_val >= 1450: risk_score += 4; reasons.append("환율 1,450원 돌파 (외환위기급)")
    elif krw_val >= 1400: risk_score += 3; reasons.append("환율 1,400원 상회 (외인 이탈)")
    elif krw_val >= 1350: risk_score += 2; reasons.append("환율 1,350원 상회")
    elif krw_val >= 1320: risk_score += 1

    # 4. 국내 증시 수급 및 추세 (코스피/코스닥 + 외인 추정) (최대 8점)
    # yfinance로는 실시간 외인 수급이 없으므로, 지수 등락폭을 통해 간접 평가
    # (일반적으로 코스피가 1% 이상 빠지면 외인 매도세가 강한 날로 간주)
    
    market_badness = 0
    
    # 코스피 상태
    if kospi_pct < -2.0: market_badness += 4; reasons.append("코스피 -2% 이상 폭락 (패닉)")
    elif kospi_pct < -1.0: market_badness += 2; reasons.append("코스피 -1% 이상 하락 (약세)")
    elif kospi_pct < -0.5: market_badness += 1
    
    # 코스닥 상태
    if kosdaq_pct < -2.5: market_badness += 4; reasons.append("코스닥 -2.5% 이상 폭락 (붕괴)")
    elif kosdaq_pct < -1.5: market_badness += 2; reasons.append("코스닥 -1.5% 이상 급락")
    elif kosdaq_pct < -0.8: market_badness += 1

    # 합산 (최대 8점으로 제한)
    total_market_score = min(market_badness, 8)
    risk_score += total_market_score

    # 점수 보정 (0~20 범위)
    risk_score = min(max(risk_score, 0), 20)

    # --- UI: 게이지 차트 (0 ~ 20) ---
    st.subheader(f"📊 현재 시장 위험도: {risk_score} / 20")
    
    # 게이지 색상 구간 설정
    steps = [
        {'range': [0, 5], 'color': "#00C853"},   # 좋음 (초록)
        {'range': [5, 10], 'color': "#FFD600"},  # 주의 (노랑)
        {'range': [10, 15], 'color': "#FF6D00"}, # 위험 (주황)
        {'range': [15, 20], 'color': "#D50000"}  # 폭락 (빨강)
    ]

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 20], 'tickwidth': 1},
            'bar': {'color': "black"},
            'steps': steps,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- 행동 가이드 (20단계 세분화) ---
    
    # 원인 박스
    if reasons:
        st.warning("**🚨 주요 위험 요인:**\n" + "\n".join([f"- {r}" for r in reasons]))
    else:
        st.success("**✅ 특이 사항 없음:** 모든 지표가 평온합니다.")

    st.markdown("### 💡 행동 가이드 (Level 1 ~ 20)")

    # 20단계 텍스트 생성
    # 로직: 점수(0~20)에 따라 메시지 결정
    
    guide_msg = ""
    guide_color = ""
    
    if risk_score >= 18:
        level_title = "Lv.18~20 [시장 붕괴 - 탈출 불가]"
        guide_msg = "이미 늦었을 수 있습니다. 투매가 투매를 부르는 공황 상태입니다. 지금 던지면 최저점일 수 있으니, 차라리 HTS를 끄고 며칠간 보지 마십시오. 신규 진입은 자살행위입니다."
        guide_color = "#FFCDD2" # 옅은 빨강 배경
    elif risk_score >= 15:
        level_title = "Lv.15~17 [폭락장 - 현금 생명]"
        guide_msg = "소나기가 아니라 태풍입니다. 코스피/코스닥이 무너지고 있습니다. 반등 시마다 물량을 줄이고 현금을 80% 이상 확보하세요."
        guide_color = "#FFCDD2"
    elif risk_score >= 12:
        level_title = "Lv.12~14 [대세 하락 - 보수적]"
        guide_msg = "외국인이 한국 시장을 떠나고 있습니다. 환율과 금리가 부담스럽습니다. 단타 실력이 없다면 쉬는 것이 돈 버는 것입니다."
        guide_color = "#FFE0B2" # 옅은 주황
    elif risk_score >= 9:
        level_title = "Lv.9~11 [경계 - 박스권 하단]"
        guide_msg = "분위기가 험악합니다. 적극적인 매수는 자제하고, 확실한 주도주(실적주) 외에는 정리가 필요합니다. 현금 50% 유지."
        guide_color = "#FFE0B2"
    elif risk_score >= 6:
        level_title = "Lv.6~8 [주의 - 변동성 확대]"
        guide_msg = "지수가 방향을 탐색 중입니다. 금리나 유가 중 하나가 거슬립니다. 몰빵 금지, 분할 매수만 유효합니다."
        guide_color = "#FFF9C4" # 옅은 노랑
    elif risk_score >= 3:
        level_title = "Lv.3~5 [보통 - 맑음]"
        guide_msg = "큰 악재는 없습니다. 개별 종목 장세입니다. 외국인 수급이 들어오는 섹터 위주로 담아보세요."
        guide_color = "#F0F4C3" # 옅은 연두
    else:
        level_title = "Lv.0~2 [최상 - 강력 매수]"
        guide_msg = "골디락스(Goldilocks)입니다. 금리, 유가, 환율 모두 안정적입니다. 주식 비중 100%로 수익을 극대화하세요!"
        guide_color = "#C8E6C9" # 옅은 초록

    # 현재 단계 표시
    st.markdown(f"""
    <div style="background-color: {guide_color}; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
        <h3 style="margin:0; color:#333;">👉 현재 상태: {level_title}</h3>
        <p style="margin-top:10px; font-size:16px; font-weight:bold;">{guide_msg}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 20단계 전체 표 (접기 기능)
    with st.expander("📜 전체 20단계 가이드라인 보기"):
        st.markdown("""
        | 위험도(Lv) | 상태 | 행동 요령 |
        |---|---|---|
        | **18~20** | 🌪️ 붕괴 | 모든 자산 매도 후 관망. HTS 삭제 권장. |
        | **15~17** | ☔️ 폭락 | 투매 동참 금지, 반등시 현금화 주력. |
        | **12~14** | 🌧️ 하락 | 보수적 대응. 현금 비중 50~70% 유지. |
        | **09~11** | ☁️ 흐림 | 신규 매수 자제. 리스크 관리 집중. |
        | **06~08** | ⛅️ 주의 | 변동성 확대. 분할 매수/매도 대응. |
        | **03~05** | 🌤️ 양호 | 개별주 장세. 실적주 위주 접근. |
        | **00~02** | ☀️ 최상 | 적극 매수. 불타기 가능 구간. |
        """)
