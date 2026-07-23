import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_collector import update_lotto_data
from src.analyzer import LottoAnalyzer
from src.predictor import LottoPredictor
from src.comparator import LottoComparator
from src.ui_components import inject_custom_css, render_lotto_balls, render_prediction_result

# 페이지 기본 설정
st.set_page_config(
    page_title="Lotto Predictor PRO",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 주입
inject_custom_css()

# --- 메인 화면 상단 (데이터 로딩 전 렌더링) ---
st.title("Lotto Predictor PRO 🎱")
st.markdown("통계적 경향성과 적합도 기반의 프로덕션 수준 로또 번호 예측기")

# 데이터 로딩 및 프로그레스 바 연동
if "lotto_df" not in st.session_state:
    st.info("💡 초기 데이터를 준비하는 중입니다... (최초 실행 시 약 1~2분 정도 소요될 수 있습니다)")
    progress_text = st.empty()
    progress_bar = st.empty()
    
    def on_progress(current, total):
        progress_text.info(f"동행복권 서버에서 데이터를 수집하고 있습니다... ({current}/{total} 회차)")
        if total > 0:
            progress_bar.progress(min(current / total, 1.0))
            
    try:
        df = update_lotto_data(progress_callback=on_progress)
        st.session_state["lotto_df"] = df
        progress_text.empty()
        progress_bar.empty()
    except Exception as e:
        st.error(f"데이터 수집 중 오류가 발생했습니다: {e}")
        st.stop()
else:
    df = st.session_state["lotto_df"]

try:
    analyzer = LottoAnalyzer(df)
    comparator = LottoComparator(df)
    
    if not df.empty:
        latest_draw = df.iloc[-1]
        recent_numbers = [int(latest_draw[f"num{i}"]) for i in range(1, 7)]
    else:
        latest_draw = None
        recent_numbers = []
        
    predictor = LottoPredictor(analyzer, recent_draw=recent_numbers)
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 사이드바 설정 ---
st.sidebar.title("🎱 설정 (Settings)")
st.sidebar.markdown("---")

num_games = st.sidebar.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

st.sidebar.subheader("규칙 활성화 (Rule Toggles)")
use_odd_even = st.sidebar.toggle("홀짝 균형 필터", value=True)
use_sum_range = st.sidebar.toggle("합계 범위 필터", value=True)
use_consecutive = st.sidebar.toggle("연속 번호 제한", value=True)
use_ac_value = st.sidebar.toggle("AC값 필터", value=True)
use_band_balance = st.sidebar.toggle("번호대 균형", value=True)
use_exclude_recent = st.sidebar.toggle("직전 회차 제외", value=True)

st.sidebar.subheader("가중치 조절 (Weights)")
w_odd_even = st.sidebar.slider("홀짝 균형 가중치", 0.0, 2.0, 1.0, 0.1)
w_sum_range = st.sidebar.slider("합계 범위 가중치", 0.0, 2.0, 1.0, 0.1)
w_ac_value = st.sidebar.slider("AC값 가중치", 0.0, 2.0, 1.0, 0.1)

config = {
    "rules": {
        "odd_even": use_odd_even,
        "sum_range": use_sum_range,
        "consecutive": use_consecutive,
        "ac_value": use_ac_value,
        "band_balance": use_band_balance,
        "exclude_recent": use_exclude_recent
    },
    "weights": {
        "odd_even": w_odd_even,
        "sum_range": w_sum_range,
        "ac_value": w_ac_value,
        "consecutive": 1.0,
        "band_balance": 1.0,
        "exclude_recent": 1.0
    }
}

# 수동 업데이트 버튼
if st.sidebar.button("🔄 최신 데이터 강제 갱신"):
    progress_text = st.sidebar.empty()
    progress_bar = st.sidebar.empty()
    
    def on_sidebar_progress(current, total):
        progress_text.info(f"업데이트 중... ({current}/{total})")
        if total > 0:
            progress_bar.progress(min(current / total, 1.0))

    try:
        df = update_lotto_data(progress_callback=on_sidebar_progress)
        st.session_state["lotto_df"] = df
        progress_text.empty()
        progress_bar.empty()
        st.sidebar.success("데이터가 성공적으로 업데이트 되었습니다.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"오류: {e}")

if latest_draw is not None:
    st.info(f"💡 **최신 {int(latest_draw['drwNo'])}회차 ({latest_draw['drwNoDate']}) 당첨 번호**")
    render_lotto_balls(recent_numbers, int(latest_draw['bonusNo']))
    st.markdown("---")

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["🎯 번호 생성", "📊 통계 대시보드", "🏆 과거 당첨 대조"])

# 1. 번호 생성 탭
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("최적 조합 생성")
        st.write("좌측 사이드바에서 규칙과 가중치를 설정한 후 아래 버튼을 클릭하세요.")
        generate_btn = st.button("🚀 번호 생성하기", type="primary", use_container_width=True)
    
    if generate_btn:
        with st.spinner("최적의 조합을 탐색 중입니다... (최대 10,000번의 시뮬레이션)"):
            best_combinations = predictor.generate_combinations(num_games, config)
            
        st.success(f"상위 {num_games}개의 추천 조합이 생성되었습니다!")
        
        # 세션 스테이트에 저장 (탭 이동 시 유지)
        st.session_state["best_combinations"] = best_combinations
        
    if "best_combinations" in st.session_state:
        for i, comb in enumerate(st.session_state["best_combinations"]):
            render_prediction_result(i + 1, comb)


# 2. 통계 대시보드 탭
with tab2:
    st.subheader("역대 당첨 통계 대시보드")
    
    if not df.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # 1. 번호별 출현 빈도
            freq = analyzer.get_frequency()
            fig1 = px.bar(
                x=freq.index, y=freq.values,
                labels={'x': '번호', 'y': '출현 횟수'},
                title="역대 번호별 출현 빈도",
                color=freq.values,
                color_continuous_scale="Viridis"
            )
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f5f5f5'))
            st.plotly_chart(fig1, use_container_width=True)
            
            # 2. 홀짝 분포
            odd_even = analyzer.get_odd_even_distribution()
            fig2 = px.pie(
                names=odd_even.index, values=odd_even.values,
                title="역대 홀짝 비율 (홀:짝)",
                hole=0.4
            )
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#f5f5f5'))
            st.plotly_chart(fig2, use_container_width=True)

        with col_chart2:
            # 3. 합계 분포
            sum_data = analyzer.get_sum_distribution()
            fig3 = px.histogram(
                x=sum_data["sums"],
                nbins=30,
                labels={'x': '번호 6개 합계'},
                title=f"당첨 번호 합계 분포 (평균: {sum_data['mean']:.1f})",
                color_discrete_sequence=['#d4af37']
            )
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f5f5f5'))
            st.plotly_chart(fig3, use_container_width=True)
            
            # 4. 번호대별 출현
            band_dist = analyzer.get_number_band_distribution()
            fig4 = px.bar(
                x=band_dist.index, y=band_dist.values,
                labels={'x': '번호대', 'y': '출현 횟수'},
                title="번호대별 출현 빈도 (10단위)",
                color_discrete_sequence=['#69c8f2']
            )
            fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f5f5f5'))
            st.plotly_chart(fig4, use_container_width=True)
            

# 3. 과거 당첨 대조 탭
with tab3:
    st.subheader("생성된 조합의 과거 성적표")
    st.write("현재 생성된 번호들이 과거에 나왔다면 몇 등을 했을까요? (5등 이상만 표시)")
    
    if "best_combinations" in st.session_state:
        for i, comb in enumerate(st.session_state["best_combinations"]):
            nums = comb["numbers"]
            st.markdown(f"#### 조합 #{i+1}")
            render_lotto_balls(nums)
            
            with st.expander(f"이 조합의 과거 기록 보기 (클릭)"):
                summary = comparator.get_best_record_summary(nums)
                st.write(f"**{summary}**")
                
                history_matches = comparator.compare_combination(nums)
                if not history_matches.empty:
                    st.dataframe(history_matches, use_container_width=True)
                else:
                    st.info("과거에 5등 이상 당첨된 적이 없는 신선한 조합입니다.")
            st.markdown("---")
    else:
        st.info("먼저 [번호 생성] 탭에서 번호를 생성해 주세요.")

# 푸터 (면책 문구)
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem; padding: 20px;">
    <b>[면책 조항]</b> 로또는 매 회차 독립 시행이므로 과거의 통계가 미래의 결과를 보장하지 않습니다.<br>
    본 애플리케이션에서 제공하는 예측 점수는 통계적 경향성에 기반한 오락 목적의 참고 자료일 뿐입니다.<br>
    지나친 몰입을 주의하시고 책임감 있는 건전한 게임 문화를 지향합니다.
</div>
""", unsafe_allow_html=True)
