import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="시장 긴급 점검",
    page_icon="📈",
    layout="centered"
)

# --- 스타일링 (CSS) ---
st.markdown("""
    <style>
    .header-title {
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
    }
    .weather-info {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
    .big-font {
        font-size:16px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    /* 현재 단계 강조 스타일 */
    .current-level {
        background-color: #ffebee;
        border-left: 5px solid #ff4b4b;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        color: #ff4b4b;
        margin-bottom: 5px;
    }
    .normal-level {
        color: #888;
        padding: 5px;
        margin-bottom: 2px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 상단: 새로고침 버튼 (요청 2번) ---
if st.button('🔄 데이터 새로고침', use_container_width=True):
    st.rerun()

# --- 함수: 날씨 가져오기 (요청 1번: 대전) ---
def get_weather(city="Daejeon"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return response.text.strip()
        return "날씨 정보 없음"
    except:
        return "N/A"

# --- 함수: 데이터 가져오기 ---
def get_data():
    try:
        tickers = {
            "tnx": "^TNX",   # 미국 10년물 국채
            "oil": "CL=F",   # WTI 유가
            "krw": "KRW=X"   # 원/달러 환율
        }
        
        data = {}
        for key, symbol in tickers.items():
            df = yf.download(symbol, period="1mo", progress=False)
            if len(df) < 2:
                # 데이터가 없을 경우를 대비해 더미 데이터라도 반환하거나 에러 처리
                if len(df) == 1: # 1개라도 있으면 복제해서 에러 방지
                    df = pd.concat([df, df])
                else:
                    raise ValueError(f"{symbol} 데이터 부족")
            data[key] = df
            
        return data, None
    except Exception as e:
        return None, e

# --- 헤더 섹션 ---
weather = get_weather("Daejeon") # 대전으로 설정
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

st.markdown(f'<div class="header-title">📈 사장님의 모닝 루틴</div>', unsafe_allow_html=True)
st.markdown(f'<div class="weather-info">📍 대전: {weather} | 🕒 {now_str} 확인</div>', unsafe_allow_html=True)

st.markdown("---")

# --- 메인 로직 ---
market_data, error = get_data()

if error:
    st.error(f"데이터 로딩 실패: {error}")
else:
    col1, col2, col3 = st.columns(3)

    def get_latest(df):
        current = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        if isinstance(current, pd.Series): current = current.item()
        if isinstance(prev, pd.Series): prev = prev.item()
        return current, prev, current - prev

    # 1. 지표 출력
    tnx_curr, _, tnx_diff = get_latest(market_data['tnx'])
    with col1:
        st.markdown('<p class="big-font">🇺🇸 국채(10y)</p>', unsafe_allow_html=True)
        st.metric("전일비", f"{tnx_curr:.3f}%", f"{tnx_diff:.3f}", delta_color="inverse")

    oil_curr, _, oil_diff = get_latest(market_data['oil'])
    with col2:
        st.markdown('<p class="big-font">🛢️ 유가(WTI)</p>', unsafe_allow_html=True)
        st.metric("전일비", f"${oil_curr:.2f}", f"{oil_diff:.2f}", delta_color="inverse")

    krw_curr, _, krw_diff = get_latest(market_data['krw'])
    with col3:
        st.markdown('<p class="big-font">🇰🇷 환율(원)</p>', unsafe_allow_html=True)
        st.metric("전일비", f"{krw_curr:.0f}원", f"{krw_diff:.1f}", delta_color="inverse")

    st.markdown("---")

    # --- 위험도 계산 및 원인 분석 (요청 6번: 원인 추가) ---
    risk_score = 0
    reasons = [] # 원인을 담을 리스트

    # 국채 금리 기준
    if tnx_curr >= 4.5: 
        risk_score += 3
        reasons.append("• 국채금리 4.5% 돌파 (심각)")
    elif tnx_curr >= 4.2: 
        risk_score += 2
        reasons.append("• 국채금리 4.2% 상회 (주의)")
    elif tnx_curr >= 4.0: 
        risk_score += 1
        reasons.append("• 국채금리 4.0% 상회")
    
    # 유가 기준
    if oil_curr >= 85: 
        risk_score += 3
        reasons.append("• 유가 $85 돌파 (인플레 우려)")
    elif oil_curr >= 80: 
        risk_score += 2
        reasons.append("• 유가 $80 상회 (부담)")
    elif oil_curr >= 75: 
        risk_score += 1
    
    # 환율 기준
    if krw_curr >= 1400: 
        risk_score += 3
        reasons.append("• 환율 1,400원 돌파 (외인 이탈)")
    elif krw_curr >= 1350: 
        risk_score += 2
        reasons.append("• 환율 1,350원 상회")
    elif krw_curr >= 1320: 
        risk_score += 1

    # 레벨 결정 (1~7단계)
    if risk_score >= 8: current_lv = 7
    elif risk_score >= 6: current_lv = 6
    elif risk_score >= 5: current_lv = 5
    elif risk_score == 4: current_lv = 4
    elif risk_score == 3: current_lv = 3
    elif risk_score >= 1: current_lv = 2
    else: current_lv = 1

    # --- 시각화: 게이지 차트 (요청 3번) ---
    st.subheader("📊 시장 압력 게이지")
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_lv,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Market Pressure (Lv.1 ~ Lv.7)"},
        gauge = {
            'axis': {'range': [1, 7], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [1, 2], 'color': "green"},
                {'range': [2, 4], 'color': "yellow"},
                {'range': [4, 6], 'color': "orange"},
                {'range': [6, 7], 'color': "red"}],
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- 행동 가이드 출력 (요청 4, 5번) ---
    st.subheader("💡 오늘의 행동 가이드")
    
    # 원인 출력
    if reasons:
        st.info("**[위험 원인 분석]**\n" + "\n".join(reasons))
    else:
        st.success("**[특이 사항 없음]** 시장 지표가 모두 안정적입니다.")

    # 7단계 정의
    levels = [
        (7, "Lv.7 [폭풍 경보]", "시장 붕괴 위험. 전량 매도 및 현금 100% 확보."),
        (6, "Lv.6 [대피 준비]", "매우 위험. 소나기가 옵니다. 현금 비중 70% 이상."),
        (5, "Lv.5 [우산 챙기기]", "위험 신호. 신규 매수 금지, 수익 난 종목 차익 실현."),
        (4, "Lv.4 [흐림]", "관망 필요. 무리한 투자 지양, 현금 50% 유지."),
        (3, "Lv.3 [구름 조금]", "중립. 우량주 위주 보유, 적극적인 매매 자제."),
        (2, "Lv.2 [맑음]", "투자 적기. 분할 매수로 접근하기 좋은 시점."),
        (1, "Lv.1 [매우 맑음]", "강력 매수. 주식 비중을 최대로 늘리세요!")
    ]

    # 리스트 출력 (현재 단계만 강조)
    st.markdown("---")
    for lv, title, desc in levels: # 7부터 1까지 역순 출력하고 싶으면 그대로, 아니면 reversed
        if lv == current_lv:
            st.markdown(f"""
            <div class="current-level">
                👉 현재 단계: {title}<br>
                {desc}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="normal-level">
                {title} - {desc}
            </div>
            """, unsafe_allow_html=True)
