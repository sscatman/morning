import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 앱 기본 설정 (모바일 친화적) ---
st.set_page_config(
    page_title="시장 긴급 점검",
    page_icon="📈",
    layout="centered" # 모바일에서는 centered가 보기 편합니다
)

# --- 스타일링 (CSS) ---
# 글자 크기를 키우고 여백을 조정하여 앱처럼 보이게 만듭니다.
st.markdown("""
    <style>
    .big-font {
        font-size:18px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 헤더 ---
st.title("📈 사장님의 모닝 루틴")
st.caption(f"최종 확인: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.markdown("---")

# --- 데이터 가져오기 함수 ---
def get_data():
    try:
        # 미국 10년물 국채 금리
        tnx = yf.Ticker("^TNX")
        tnx_hist = tnx.history(period="2d") # 전일 대비 비교를 위해 2일치
        
        # WTI 유가
        oil = yf.Ticker("CL=F")
        oil_hist = oil.history(period="2d")
        
        return tnx_hist, oil_hist, None # 성공
    except Exception as e:
        return None, None, e # 실패

# --- 메인 로직 ---
tnx_data, oil_data, error = get_data()

if error:
    st.error(f"데이터를 가져오는데 실패했습니다.\n{error}")
else:
    # 2단 레이아웃 설정 (화면을 반으로 나눔)
    col1, col2 = st.columns(2)

    # 1. 미국 10년물 국채 금리 (왼쪽)
    with col1:
        current_tnx = tnx_data['Close'].iloc[-1]
        prev_tnx = tnx_data['Close'].iloc[-2]
        diff_tnx = current_tnx - prev_tnx
        
        st.markdown('<p class="big-font">🇺🇸 미국 10년물 국채</p>', unsafe_allow_html=True)
        
        # 색상 로직: 4.2% 넘으면 빨간색 경고
        if current_tnx >= 4.5:
            st.error(f"🚨 {current_tnx:.2f}% (패닉!)")
        elif current_tnx >= 4.2:
            st.warning(f"⚠️ {current_tnx:.2f}% (경고)")
        else:
            st.success(f"✅ {current_tnx:.2f}% (안정)")
            
        st.metric(label="전일 대비", value=f"{current_tnx:.2f}%", delta=f"{diff_tnx:.2f}%", delta_color="inverse")

    # 2. WTI 국제 유가 (오른쪽)
    with col2:
        current_oil = oil_data['Close'].iloc[-1]
        prev_oil = oil_data['Close'].iloc[-2]
        diff_oil = current_oil - prev_oil

        st.markdown('<p class="big-font">🛢️ 국제 유가 (WTI)</p>', unsafe_allow_html=True)
        
        if current_oil >= 85:
            st.error(f"🚨 ${current_oil:.2f} (위험!)")
        else:
            st.success(f"✅ ${current_oil:.2f} (안정)")

        st.metric(label="전일 대비", value=f"${current_oil:.2f}", delta=f"{diff_oil:.2f}", delta_color="inverse")

    st.markdown("---")

    # 3. 사장님 포트폴리오 조언
    # 10년물 금리와 유가 데이터를 변수로 가져와서 판단 로직에 사용
    current_tnx_val = tnx_data['Close'].iloc[-1]
    current_oil_val = oil_data['Close'].iloc[-1]

    st.subheader("💡 오늘의 행동 가이드")
    
    warning_count = 0
    if current_tnx_val >= 4.2: warning_count += 1
    if current_oil_val >= 85: warning_count += 1
    
    if warning_count >= 2:
        st.info("""
        **[매우 위험]** 소나기가 내립니다 ☔️
        * IONQ, 코스닥 등 변동성 큰 주식은 **관망**하세요.
        * 현금 비중을 늘리는 것을 추천합니다.
        """)
    elif warning_count == 1:
        st.info("""
        **[주의 필요]** 경고등이 하나 켜졌습니다 ⚠️
        * 신규 매수는 자제하시고 시장을 지켜보세요.
        * 외국인 매도세가 거세질 수 있습니다.
        """)
    else:
        st.info("""
        **[투자 좋음]** 날씨 맑음 ☀️
        * 현재 시장 지표가 안정적입니다.
        * 보유 종목(반도체, 성장주)을 즐기세요!
        """)

# --- 새로고침 버튼 ---
if st.button('🔄 데이터 새로고침', use_container_width=True):
    st.rerun()
