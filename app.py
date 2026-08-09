import streamlit as st
import requests
import pandas as pd
import time

# 웹페이지 기본 설정
st.set_page_config(page_title="대구 주요 아파트 실시간 시세", layout="wide")

# 1. 모니터링할 대구 아파트 단지 목록 (아파트명: 단지번호)
# Step 1에서 찾은 실제 단지번호로 수정해주세요!
TARGET_APTS = {
    "센트로팰리스": "13620",
    "범어자이르네": "182577",
    "힐스테이트대구역": "128323"
    # 필요에 따라 10개까지 추가...
}

@st.cache_data(ttl=600)  # 10분간 데이터 캐싱 (네이버 차단 방지)
def fetch_naver_land_data(complex_no):
    """네이버 부동산 API를 통해 단지별 매물 정보를 가져오는 함수"""
    url = f"https://new.land.naver.com/api/articles/complex/{complex_no}?realEstateType=APT&tradeType=&page=1&order=prc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://new.land.naver.com/complexes/{complex_no}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articleList", [])
            
            result = []
            for item in articles:
                result.append({
                    "동": item.get("buildingName", "-"),
                    "거래방식": item.get("tradeTypeName", "-"),
                    "가격": item.get("dealOrWarrantPrc", "-"),
                    "층수": item.get("floorInfo", "-"),
                    "전용면적(㎡)": item.get("area2", "-"),
                    "방향": item.get("direction", "-"),
                    "매물특징": item.get("articleFeatureDesc", "-"),
                    "확인일자": item.get("articleConfirmYmd", "-")
                })
            return pd.DataFrame(result)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

# --- UI 화면 구성 ---
st.title("🏢 대구 아파트 실시간 매물 현황")
st.caption("네이버 부동산 데이터 기반 · 공유용 매물 시세 모니터링")

# 우측 상단 업데이트 버튼
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🔄 시세 실시간 새로고침", use_container_width=True):
        st.cache_data.clear()  # 캐시 삭제 후 다시 불러오기
        st.rerun()

# 사이드바 필터 설정
st.sidebar.header("🔍 검색 및 필터")
selected_apt_name = st.sidebar.selectbox("아파트 선택", list(TARGET_APTS.keys()))
trade_filter = st.sidebar.multiselect("거래 유형", ["매매", "전세", "월세"], default=["매매", "전세"])

# 데이터 불러오기
complex_id = TARGET_APTS[selected_apt_name]
with st.spinner(f"'{selected_apt_name}' 최신 매물 불러오는 중..."):
    df = fetch_naver_land_data(complex_id)

# 데이터 출력
if not df.empty:
    # 거래 유형 필터링
    if trade_filter:
        df = df[df["거래방식"].isin(trade_filter)]
    
    # 상단 메트릭 요약
    total_count = len(df)
    trade_count = len(df[df["거래방식"] == "매매"])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("총 등록 매물 수", f"{total_count}개")
    m2.metric("매매 매물", f"{trade_count}개")
    m3.metric("선택한 단지", selected_apt_name)
    
    st.markdown("---")
    
    # 매물 상세 테이블 출력
    st.subheader(f"📋 {selected_apt_name} 매물 리스트")
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "가격": st.column_config.TextColumn("매물가", help="억 원 단위"),
            "매물특징": st.column_config.TextColumn("특징", width="large")
        }
    )
else:
    st.warning("현재 등록된 매물이 없거나 데이터를 가져오지 못했습니다.")