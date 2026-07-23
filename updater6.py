import re

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove old random button
old_btn = """if st.sidebar.button("🎲 규칙 무작위 선정", use_container_width=True):
    for rule_name in rules_config.keys():
        st.session_state[f"rule_{rule_name}"] = random.choice([True, False])
"""
content = content.replace(old_btn, "")

# 2. Add new random button and caption
new_btns = """generate_clicked = st.sidebar.button("번호 생성하기", key="generate_button", type="primary", use_container_width=True)
random_generate_clicked = st.sidebar.button("🎲 조합별 랜덤 규칙 생성", key="random_generate_button", use_container_width=True)
st.sidebar.caption("위 버튼을 누르면 각 게임마다 적용되는 규칙이 무작위로 선택되어, 다채로운 패턴의 조합을 생성합니다.")"""
content = content.replace('generate_clicked = st.sidebar.button("번호 생성하기", key="generate_button", type="primary", use_container_width=True)', new_btns)

# 3. Modify condition for main area
content = content.replace('if not generate_clicked:', 'if not generate_clicked and not random_generate_clicked:')

# 4. Modify generation loop
old_loop = """            with st.spinner("통계적 필터를 적용하여 수만 개의 난수 중 최적의 조합을 추출 중입니다..."):
                for i in range(num_games):
                    combination, ignored_rules, explanation = predictor.generate_combination(selected_rules, include_nums, exclude_nums)
                    generated_combinations.append((combination, ignored_rules, explanation))"""

new_loop = """            with st.spinner("통계적 필터를 적용하여 수만 개의 난수 중 최적의 조합을 추출 중입니다..."):
                for i in range(num_games):
                    if random_generate_clicked:
                        current_game_rules = [r for r in list(rules_config.keys()) if random.choice([True, False])]
                    else:
                        current_game_rules = selected_rules
                        
                    combination, ignored_rules, explanation = predictor.generate_combination(current_game_rules, include_nums, exclude_nums)
                    
                    if random_generate_clicked:
                        explanation.insert(0, "🎲 **랜덤 규칙 적용**: 이 조합은 무작위로 선택된 규칙 세트를 기반으로 생성되었습니다.")
                        
                    generated_combinations.append((combination, ignored_rules, explanation))"""

content = content.replace(old_loop, new_loop)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update 6 complete")
