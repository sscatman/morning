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
# 🔑 사장님 전용 설정 (API 키가 없어도 프로그램은 작동합니다)
MY_GEMINI_API_KEY = ""  
# =========================================================

# --- 앱 기본 설정 ---
st.set_page_config(
    page_title="위험도 분석 V0.49", 
    page_icon="🦅",
    layout="wide"
)

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

    .guide-box { padding: 25px; background-color: #ffffff; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; color: #111 !important; }
    .guide-header { font-size: 20px; font-weight: 800; margin-bottom: 15px; color: #1565c0 !important; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
    .guide-section-title { font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; color: #1565c0 !important; }
    .guide-text { font-size: 15px; line-height: 1.7; margin-bottom: 10px; color: #333 !important; }
    .portfolio-card { background-color: #f0f4f8; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 5px solid #1565c0; }
    .portfolio-item { margin-bottom: 8px; font-size: 14.5px; line-height: 1.6; }
    
    .news-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
    .news-title { font-weight: 600; text-decoration: none; color: #333; }
    .news-title:hover { color: #1565c0; text-decoration: underline; }
    .fed-badge { background-color: #e3f2fd; color: #1565c0; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ Eagle Eye V0.49")
    api_key_input = MY_GEMINI_API_KEY if MY_GEMINI_API_KEY else ""
    if not api_key_input:
        api_key_input = st.text_input("🔑 Gemini API 키 입력", type="password", placeholder="키를 넣으면 AI 분석이 활성화됩니다.")
    
    if st.button('🔄 데이터 새로고침'):
        st.rerun()
    if api_key_input: st.success("✅ AI 모드 작동 중")
    else: st.info("ℹ️ 기본 분석 엔진 작동 중")

# --- 데이터 수집 함수 ---
def get_weather(city="Daejeon"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t&_={int(time.time())}"
        res = requests.get(url, timeout=2)
        return res.text.strip() if res.status_code == 200 else "N/A"
    except: return "N/A"

# --- [수정] 수급 정보 크롤링 (지수별 전용 페이지 타겟팅) ---
def get_market_investors():
    headers = { 'User-Agent': 'Mozilla/5.0' }
    result = { 
        "kospi_foreigner": 0, 
        "futures_foreigner": 0, 
        "raw_data": {"kospi_foreigner": "0", "futures_foreigner": "0"} 
    }
    
    def parse_amount(text):
        try: 
            # 억 단위 콤마 제거 및 정수 변환
            text = re.sub(r'[^\d\-]', '', text)
            return int(text) if text else 0
        except: return 0

    try:
        # 1. 코스피 수급 (네이버 금융 코스피 메인)
        url_kospi = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
        res_kospi = requests.get(url_kospi, headers=headers, timeout=5)
        soup_kospi = BeautifulSoup(res_kospi.content.decode('euc-kr', 'replace'), 'html.parser')
        
        # dl.lst_kos_info -> dd (개인, 외국인, 기관 순서)
        kospi_items = soup_kospi.select('.lst_kos_info dd span')
        if len(kospi_items) >= 2:
            # 보통 0:개인, 1:외국인, 2:기관
            val_str = kospi_items[1].text.strip()
            result["kospi_foreigner"] = parse_amount(val_str)
            result["raw_data"]["kospi_foreigner"] = val_str

        # 2. 선물 수급 (네이버 금융 선물 메인)
        # 선물 페이지는 구조가 다를 수 있어 메인 페이지의 리스트를 활용하는 것이 안정적일 수 있으나
        # 여기서는 선물 전용 데이터를 찾기 위해 sise_main을 파싱 시도
        url_main = "https://finance.naver.com/sise/"
        res_main = requests.get(url_main, headers=headers, timeout=5)
        soup_main = BeautifulSoup(res_main.content.decode('euc-kr', 'replace'), 'html.parser')
        
        # '선물' 키워드가 있는 테이블이나 리스트 찾기
        # 보통 #tab_sel1_deal_trend > table 구조 사용
        # 간편하게: 메인 페이지 내 선물 외국인 수치 직접 찾기 어려우므로
        # 투자자별 매매동향 페이지 상세 파싱 시도
        url_investor = "https://finance.naver.com/sise/investorDealTrendDay.naver?bizdate=" + datetime.now().strftime("%Y%m%d") + "&sosok=00"
        # 위 URL은 복잡하므로, 다시 메인페이지의 전광판 데이터 활용
        
        # 대안: 크롤링이 까다로운 선물 데이터는 값이 없으면 0으로 두되, 
        # 코스피 데이터라도 확실하게 보여주는 전략
        
        # 선물 데이터 보강 (메인 페이지 파싱 재시도)
        # HTML 구조상 선물 외국인은 특정 ID가 없음. 
        # 따라서 수급은 코스피 위주로 확실히 하고, 선물은 보조로 둠.
        
    except Exception as e:
        # print(f"Error scraping investors: {e}")
        pass
        
    return result

def get_financial_news():
    news = {"tech": [], "kr": []}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get("https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258", headers=headers, timeout=5)
        soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')
        items = soup.select('.newsList li dl')
        for item in items[:5]:
            at = item.select_one('.articleSubject a')
            if at: news["tech"].append({"title": at.text.strip(), "link": "https://finance.naver.com" + at['href']})
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers=headers, timeout=5)
        soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')
        items = soup.select('.block1 a')
        for at in items[:5]:
            news["kr"].append({"title": at.text.strip(), "link": "https://finance.naver.com" + at['href']})
    except: pass
    return news

def get_all_data():
    tickers = {
        "tnx": "^TNX", "oil": "CL=F", "krw": "KRW=X",
        "nas": "^IXIC", "sp5": "^GSPC", "sox": "^SOX",
        "kospi": "^KS11", "kosdaq": "^KQ11",
        "gold": "GC=F", "silver": "SI=F", "btc": "BTC-USD", "vix": "^VIX",
        "laes": "LAES" 
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

# --- 기본 분석 알고리즘 (API 키 없을 때 실행) ---
def get_basic_report(m, inv, score):
    res = {"headline": "", "portfolio": ""}
    
    if score >= 60: res["headline"] = "🚨 고위험 국면입니다. 자산 보호를 최우선으로 해야 합니다."
    elif score >= 40: res["headline"] = "⚖️ 변동성이 큰 혼조세입니다. 방어적인 포지션이 유리합니다."
    elif score >= 20: res["headline"] = "⛅ 완만한 흐름입니다. 주도주 중심의 선별적 대응이 필요합니다."
    else: res["headline"] = "☀️ 시장 에너지가 매우 좋습니다. 적극적인 투자 기회입니다."

    lines = []
    # KODEX 반도체
    if m['sox']['pct'] > 1: lines.append("✅ <b>KODEX 반도체:</b> 반도체 지수 강세로 추가 상승 기대")
    else: lines.append("⏺ <b>KODEX 반도체:</b> 시장 흐름 주시하며 비중 유지")

    # KODEX 코스닥 150
    if m['kosdaq']['pct'] > 0: lines.append("✅ <b>KODEX 코스닥 150:</b> 국내 중소형주 온기 확산 중")
    else: lines.append("⚠️ <b>KODEX 코스닥 150:</b> 코스닥 변동성 확대에 따른 주의 요망")

    # 아이온큐
    if m['nas']['pct'] > 0: lines.append("🚀 <b>아이온큐(IONQ):</b> 미 기술주 상승 랠리 편승 중")
    else: lines.append("⏺ <b>아이온큐(IONQ):</b> 성장주 밸류에이션 부담 체크 필요")

    # 실스크(LAES)
    if m['laes']['pct'] > 0: lines.append("🟡 <b>실스크(LAES):</b> 개별 모멘텀 지속 여부 확인 필요")
    else: lines.append("⏺ <b>실스크(LAES):</b> 하방 경직성 테스트 구간")

    res["portfolio"] = "<br>".join(lines)
    return res

# --- AI 분석 함수 ---
def get_ai_portfolio_analysis(api_key, m, inv, score):
    if not api_key: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"""당신은 전문 자산운용가입니다. [보유종목: KODEX반도체, KODEX코스닥150, 아이온큐(IONQ), 실스크(LAES)]에 대해 위험도 {score}점인 현재 시장 상황을 분석하여 전략을 JSON 형식으로 짜주세요."""
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt + str(m)}]}]}, timeout=10)
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(match.group(0))
        return None
    except: return None

# --- 실행부 ---
weather = get_weather()
kst_now = datetime.utcnow() + timedelta(hours=9)
st.markdown(f"""<div class="header-title">🦅 Eagle Eye V0.49</div><div class="sub-info">📍 대전: {weather} | 🕒 {kst_now.strftime('%Y-%m-%d %H:%M')}</div>""", unsafe_allow_html=True)

data, err = get_all_data()
inv = get_market_investors()
news = get_financial_news()

if data:
    # --- 게이지 UI 함수 ---
    def mini_gauge(title, d, min_v, max_v, mode='risk', unit=''):
        val = d['val']
        pct = max(0, min(100, (val - min_v) / (max_v - min_v) * 100))
        grad = "linear-gradient(90deg, #4CAF50 0%, #FFEB3B 50%, #F44336 100%)" if mode=='risk' else "linear-gradient(90deg, #2196F3 0%, #EEEEEE 50%, #F44336 100%)"
        st.markdown(f"""<div class="mini-gauge-container"><div class="mini-gauge-title"><span>{title}</span><span>{val:,.2f}{unit} ({d['pct']:+.2f}%)</span></div><div class="mini-gauge-track" style="background:{grad}"><div class="mini-gauge-pointer" style="left:{pct}%"></div></div><div class="mini-gauge-labels"><span>{min_v}</span><span>{max_v}</span></div></div>""", unsafe_allow_html=True)

    # 섹션 1: 주요 지표 현황
    st.subheader("📈 주요 지표 현황")
    c1, c2, c3 = st.columns(3)
    with c1:
        mini_gauge("🇺🇸 국채 10년", data['tnx'], 3.0, 5.5, 'risk', '%')
        mini_gauge("🇺🇸 나스닥", data['nas'], 15000, 40000, 'stock') 
        mini_gauge("🇰🇷 코스피", data['kospi'], 2000, 8000, 'stock') # 기준 변경 8000
    with c2:
        mini_gauge("🛢️ WTI 유가", data['oil'], 60, 100, 'risk', '$')
        mini_gauge("🇺🇸 S&P 500", data['sp5'], 4500, 10000, 'stock')
        mini_gauge("🇰🇷 코스닥", data['kosdaq'], 600, 3000, 'stock') 
    with c3:
        mini_gauge("🇰🇷 환율", data['krw'], 1300, 1550, 'risk', '원')
        mini_gauge("💾 반도체(SOX)", data['sox'], 3000, 10000, 'stock') 
        
        # 수급 정보 표시 로직 수정 (데이터 없으면 0 대신 '장 마감/집계중' 표시 고민이나, 일단 값 표시에 집중)
        k_val = inv['kospi_foreigner']
        k_str = f"{k_val}억" if k_val != 0 else "집계 중"
        k_color = "#d62728" if k_val > 0 else "#1f77b4" if k_val < 0 else "#666"
        
        # 선물은 크롤링 난이도로 인해 값이 없으면 표시 생략하거나 0 처리
        f_val = inv['futures_foreigner']
        f_str = f"{f_val}억" if f_val != 0 else "-"
        
        st.markdown(f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; margin-top:5px;">
            <p style="margin:0; font-size:14px; color:#333;">💰 <b>외국인 수급 (코스피)</b></p>
            <p style="margin:5px 0 0 0; font-size:18px; font-weight:bold; color:{k_color};">{k_str}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 섹션 2: 대체 자산 & 공포지수
    st.subheader("🛡️ 대체 자산 & 공포지수")
    c7, c8, c9, c10 = st.columns(4)
    with c7: mini_gauge("🟡 금(Gold)", data['gold'], 2000, 10000, 'stock', '$') 
    with c8: mini_gauge("⚪ 은(Silver)", data['silver'], 20, 150, 'stock', '$') 
    with c9: mini_gauge("₿ 비트코인", data['btc'], 0, 200000, 'stock', '$') 
    with c10: mini_gauge("😨 VIX(공포)", data['vix'], 10, 50, 'risk') 

    # --- 위험도 산정 ---
    def calc_r(v, min_v, max_v): return max(0, min(100, (v - min_v) / (max_v - min_v) * 100))
    risk_score = int((calc_r(data['tnx']['val'], 3.5, 5.0) + calc_r(data['oil']['val'], 65, 100) + calc_r(data['krw']['val'], 1350, 1550) + calc_r(data['vix']['val'], 15, 35) + calc_r(-data['sox']['pct'], 0, 10) + calc_r(-min(data['kospi']['pct'], data['kosdaq']['pct']), 0, 10) + calc_r(-inv['kospi_foreigner']/10, 0, 500)) / 7)
    
    st.subheader(f"📊 종합 시장 위험도: {risk_score}점")
    
    # --- 보고서 출력 ---
    report = get_ai_portfolio_analysis(api_key_input, data, inv, risk_score)
    mode_label = "🤖 AI 애널리스트" if report else "⚙️ 기본 분석 엔진"
    if not report: report = get_basic_report(data, inv, risk_score)
    
    st.markdown(f"""
    <div class="guide-box">
        <div class="guide-header">🦅 {mode_label} 브리핑</div>
        <div class="guide-section-title">1. 시장 총평</div>
        <div class="guide-text"><b>{report.get('headline', '분석 실패')}</b></div>
        <div class="guide-section-title">2. 주식 운영 가이드</div>
        <div class="portfolio-card">{report.get('portfolio', '데이터 분석 실패').replace('\\n', '<br>')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    n1, n2 = st.columns(2)
    with n1:
        st.markdown("### 🇺🇸 글로벌 테크 뉴스")
        for n in news['tech']: st.markdown(f"""<div class="news-item"><span class="fed-badge">USA</span><a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a></div>""", unsafe_allow_html=True)
    with n2:
        st.markdown("### 🇰🇷 국내 시장/반도체 뉴스")
        for n in news['kr']: st.markdown(f"""<div class="news-item"><span class="fed-badge">KOR</span><a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a></div>""", unsafe_allow_html=True)

time.sleep(300)
st.rerun()
