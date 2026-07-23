"""
UI 컴포넌트 모듈 (ui_components.py)
Streamlit 기본 UI를 덮어쓰는 커스텀 CSS 및 로또 공 렌더링 함수들을 포함합니다.
"""

import streamlit as st

def inject_custom_css():
    """
    애플리케이션 전반에 적용되는 커스텀 CSS를 주입합니다.
    웹 폰트 로드 및 다크/골드 테마를 보강합니다.
    """
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Pretendard:wght@400;600&display=swap');

    /* 전체 폰트 적용 */
    html, body, [class*="css"]  {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif !important;
    }
    
    /* 제목 폰트 (Playfair Display) */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #d4af37 !important; /* Gold */
    }

    /* 로또 공 스타일링 */
    .lotto-ball {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 45px;
        height: 45px;
        border-radius: 50%;
        color: white;
        font-weight: 600;
        font-size: 1.2rem;
        margin: 0 5px;
        box-shadow: inset -3px -3px 6px rgba(0,0,0,0.3), 2px 2px 5px rgba(0,0,0,0.2);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    /* 보너스 공은 조금 더 작거나 다르게 표시할 수 있으나 통일감 부여 */
    .bonus-plus {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 45px;
        color: #d4af37;
        font-weight: bold;
        font-size: 1.5rem;
        margin: 0 5px;
    }

    /* 카드형 컨테이너 (결과창 등) */
    .result-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 적합도 점수 배지 */
    .score-badge {
        background: linear-gradient(135deg, #d4af37, #b5952f);
        color: #121212;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def get_ball_color(number: int) -> str:
    """
    번호 구간별 공식 로또 공 색상을 반환합니다.
    """
    if 1 <= number <= 10:
        return "#fbc400" # 노랑
    elif 11 <= number <= 20:
        return "#69c8f2" # 파랑
    elif 21 <= number <= 30:
        return "#ff7272" # 빨강
    elif 31 <= number <= 40:
        return "#aaaaaa" # 회색
    else:
        return "#b0d840" # 초록

def render_lotto_balls(numbers: list[int], bonus: int = None):
    """
    숫자 리스트를 받아 로또 공 형태의 HTML로 렌더링합니다.
    """
    html = '<div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-start; margin: 10px 0;">'
    
    # 일반 번호 6개
    for num in sorted(numbers):
        color = get_ball_color(num)
        html += f'<div class="lotto-ball" style="background-color: {color};">{num}</div>'
        
    # 보너스 번호 (있는 경우)
    if bonus:
        html += '<div class="bonus-plus">+</div>'
        color = get_ball_color(bonus)
        html += f'<div class="lotto-ball" style="background-color: {color};">{bonus}</div>'
        
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_prediction_result(rank: int, comb_data: dict):
    """
    예측된 단일 조합과 그 설명(details)을 카드 형태로 렌더링합니다.
    """
    numbers = comb_data["numbers"]
    score = comb_data["score"]
    details = comb_data["details"]
    
    html = f"""
    <div class="result-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; padding: 0;">조합 #{rank}</h3>
            <div class="score-badge">적합도: {score:.1f}점</div>
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    # 공 렌더링
    render_lotto_balls(numbers)
    
    # 설명 렌더링
    details_html = '<ul style="color: #bbb; font-size: 0.9rem; margin-top: 15px;">'
    for desc in details:
        details_html += f'<li>{desc}</li>'
    details_html += '</ul></div>'
    
    st.markdown(details_html, unsafe_allow_html=True)
