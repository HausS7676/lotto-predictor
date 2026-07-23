import re
import os

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update rules_config to add 3 new rules
new_rules_config = '''rules_config = {
    "쌍수 제한 (Double Digits Limit)": {
        "desc": "11, 22, 33, 44 같은 쌍수(쌍둥이 숫자)가 조합 내에 2개 이상 나오지 않게 제한합니다.",
        "default": True
    },
    "3의 배수 비율 필터 (Multiples of 3)": {
        "desc": "3의 배수(3, 6, 9...)가 1~3개만 포함되도록 조절합니다.",
        "default": True
    },
    "장기 미출현 번호 포함 (Cold Number Inclusion)": {
        "desc": "최근 10회차 동안 한 번도 나오지 않은 번호를 무조건 1개 이상 포함시킵니다.",
        "default": True
    },
    "홀짝 균형 (Odd/Even Balance)": {
        "desc": "홀수와 짝수의 비율이 가장 흔한 2:4, 3:3, 4:2 중 하나가 되도록 제한합니다.",
        "default": True
    },
    "총합 구간 필터 (Sum Range)": {
        "desc": "6개 번호의 합계가 통계적으로 가장 집중되는 100~170 사이에 속하도록 합니다.",
        "default": True
    },
    "연속 번호 제한 (Consecutive Limit)": {
        "desc": "3개 이상의 번호가 나란히 연속되는 극단적인 패턴을 제외합니다.",
        "default": True
    },
    "AC값 필터 (Arithmetic Complexity)": {
        "desc": "번호들 간의 차이(간격)의 다양성이 7 이상이 되도록 하여 예측 불확실성을 높입니다.",
        "default": True
    },
    "번호대 균형 (Band Balance)": {
        "desc": "특정 10번대 구간(예: 10~19)에 4개 단위를 넘지 않도록 균형을 맞춥니다.",
        "default": True
    },
    "직전 회차 완전 제외 (Exclude Recent)": {
        "desc": "직전 회차에 나왔던 당첨 번호는 이번 회차 조합에서 완전히 제외합니다.",
        "default": False
    },
    "고저 비율 (High/Low Balance)": {
        "desc": "1~22(저) 번호와 23~45(고) 번호의 비율이 2:4, 3:3, 4:2를 이루도록 균형을 맞춥니다.",
        "default": True
    },
    "끝수 중복 제한 (Last Digit Check)": {
        "desc": "같은 끝자리 번호(예: 11, 21, 31)가 3개 이상 중복되지 않도록 방지합니다.",
        "default": True
    },
    "이월수 포함 필터 (Carryover Number)": {
        "desc": "직전 회차 번호 중 최소 1개가 이번 회차에 이월되도록 고정합니다. (직전 제외 규칙과 충돌 주의)",
        "default": False
    },
    "소수/합성수 균형 (Prime/Composite Balance)": {
        "desc": "조합 내에 소수(2,3,5,7...)가 1~3개 포함되도록 적절히 섞습니다.",
        "default": True
    }
}'''

content = re.sub(r'rules_config = {.*?} # type: ignore', new_rules_config, content, flags=re.DOTALL) # Ensure we don't accidentally match
content = re.sub(r'rules_config = {.*?\n}\n', new_rules_config + '\n\n', content, flags=re.DOTALL)


# 2. Update LottoPredictor.__init__ to define self.cold_numbers
init_pattern = r'(self\.last_draw_numbers = self\.data\.iloc\[-1\]\[self\.all_numbers\]\.values\.tolist\(\)\n        else:\n            self\.freq_sorted_numbers = list\(range\(1, 46\)\)\n            self\.last_draw_numbers = \[\])'
new_init = '''self.last_draw_numbers = self.data.iloc[-1][self.all_numbers].values.tolist()
            if len(self.data) >= 10:
                last_10_flat = self.data.iloc[-10:][self.all_numbers].values.flatten()
                self.cold_numbers = [n for n in range(1, 46) if n not in last_10_flat]
            else:
                self.cold_numbers = list(range(1, 46))
        else:
            self.freq_sorted_numbers = list(range(1, 46))
            self.last_draw_numbers = []
            self.cold_numbers = list(range(1, 46))'''
content = re.sub(init_pattern, new_init, content)


# 3. Update LottoPredictor.check_filters to include 3 new checks
filter_pattern = r'(if "홀짝 균형 \(Odd/Even Balance\)" in rules_to_apply:)'
new_filters = '''if "쌍수 제한 (Double Digits Limit)" in rules_to_apply:
            double_digits = [11, 22, 33, 44]
            double_count = sum(1 for x in comb if x in double_digits)
            if double_count > 1:
                return False, "쌍수 제한 (Double Digits Limit)"
                
        if "3의 배수 비율 필터 (Multiples of 3)" in rules_to_apply:
            multiple_3_count = sum(1 for x in comb if x % 3 == 0)
            if multiple_3_count not in [1, 2, 3]:
                return False, "3의 배수 비율 필터 (Multiples of 3)"
                
        if "장기 미출현 번호 포함 (Cold Number Inclusion)" in rules_to_apply:
            cold_count = sum(1 for x in comb if x in self.cold_numbers)
            if cold_count < 1:
                return False, "장기 미출현 번호 포함 (Cold Number Inclusion)"
                
        if "홀짝 균형 (Odd/Even Balance)" in rules_to_apply:'''
content = re.sub(filter_pattern, new_filters, content)


# 4. Update LottoPredictor.generate_combination
gen_pattern = r'def generate_combination\(self, rules_to_apply\):.*?def compare_with_past_results'
new_gen = '''def generate_combination(self, rules_to_apply, include_nums=None, exclude_nums=None):
        current_rules = list(rules_to_apply)
        ignored_rules = []
        include_nums = include_nums or []
        exclude_nums = exclude_nums or []
        
        while True:
            tries = 0
            while tries < 5000: # 5천번 시도
                base_numbers = self._generate_candidate_numbers()
                
                # Exclude
                base_numbers = [n for n in base_numbers if n not in exclude_nums]
                
                available_pool = [n for n in range(1, 46) if n not in base_numbers and n not in exclude_nums]
                while len(base_numbers) < 6:
                    if not available_pool:
                        break
                    chosen = random.choice(available_pool)
                    base_numbers.append(chosen)
                    available_pool.remove(chosen)
                
                comb_candidates = include_nums.copy()
                remaining_slots = 6 - len(comb_candidates)
                fillers = [n for n in base_numbers if n not in include_nums]
                
                if len(fillers) >= remaining_slots:
                    comb_candidates.extend(random.sample(fillers, remaining_slots))
                else:
                    comb_candidates.extend(fillers)
                
                if len(comb_candidates) < 6:
                    # Very rare edge case fallback
                    fallback_pool = [n for n in range(1, 46) if n not in comb_candidates and n not in exclude_nums]
                    if len(fallback_pool) >= (6 - len(comb_candidates)):
                        comb_candidates.extend(random.sample(fallback_pool, 6 - len(comb_candidates)))
                
                comb = sorted(comb_candidates[:6])
                
                if not all(x in comb for x in include_nums):
                    tries += 1
                    continue
                if any(x in comb for x in exclude_nums):
                    tries += 1
                    continue
                
                is_valid, _ = self.check_filters(comb, current_rules)
                if is_valid:
                    explanation = [f"• **빈도 기반 혼합**: 과거 당첨 빈도가 높은 번호와 낮은 번호를 적절히 섞어 초기 조합을 구성했습니다."]
                    if include_nums:
                        explanation.append(f"• **고정수 포함**: 사용자가 지정한 {include_nums} 번호가 고정 포함되었습니다.")
                    if exclude_nums:
                        explanation.append(f"• **제외수 필터**: 사용자가 지정한 제외수들은 풀에서 제거되었습니다.")
                    for rule in current_rules:
                        explanation.append(f"• **{rule}**: 해당 필터의 통계적 조건을 완벽하게 통과했습니다.")
                    return comb, ignored_rules, explanation
                
                tries += 1
                
            if current_rules:
                dropped = current_rules.pop()
                ignored_rules.append(dropped)
            else:
                explanation = [f"• **무작위 추출**: 모든 조건이 해제되어 필터 없이 추출되었습니다."]
                return sorted(random.sample(range(1, 46), 6)), ignored_rules, explanation

    def compare_with_past_results'''
content = re.sub(gen_pattern, new_gen, content, flags=re.DOTALL)


# 5. UI Updates
ui_replace_pattern = r'(if not historical_df\.empty:.*?st\.sidebar\.markdown\("---"\))'
new_ui_start = '''generate_clicked = st.sidebar.button("번호 생성하기", key="generate_button", type="primary", use_container_width=True)

if not generate_clicked:
    if not historical_df.empty:
        st.success(f"✅ 동행복권 1회차부터 {historical_df['회차'].max()}회차까지 총 {len(historical_df)}개의 실제 당첨 데이터가 동기화되었습니다.")
        
        st.markdown("---")
        st.subheader("🏆 최근 5회차 1등 당첨 번호 분석")
        st.markdown("본격적인 번호 생성 전, 최근 당첨 번호들이 이 시스템의 통계적 필터 규칙들을 얼마나 만족했는지 확인해보세요.")
        
        recent_draws = historical_df.tail(5).iloc[::-1]
        for _, draw in recent_draws.iterrows():
            round_num = int(draw['회차'])
            latest_numbers = [int(draw[f'번호{i}']) for i in range(1, 7)]
            bonus_num = int(draw['보너스'])
            
            with st.expander(f"제 {round_num}회차 당첨 번호 분석"):
                num_display = "".join([f"<span class='number-circle'>{num}</span>" for num in latest_numbers])
                st.markdown(f"<div style='margin: 10px 0;'><p>{num_display} <span style='font-size: 1.5rem; vertical-align: middle; margin: 0 10px;'>+</span> <span class='number-circle' style='background-color: #ffc107; color: black;'>{bonus_num}</span></p></div>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                rules_list = list(rules_config.keys())
                half = len(rules_list) // 2 + len(rules_list) % 2
                
                for i, rule_name in enumerate(rules_list):
                    is_valid, _ = predictor.check_filters(latest_numbers, [rule_name])
                    target_col = col1 if i < half else col2
                    if is_valid:
                        target_col.markdown(f"<span style='color: #28a745;'>✅ {rule_name}</span>", unsafe_allow_html=True)
                    else:
                        target_col.markdown(f"<span style='color: #dc3545;'>❌ {rule_name}</span>", unsafe_allow_html=True)
    else:
        st.error("데이터 동기화에 실패했습니다. 네트워크를 확인해주세요.")

st.sidebar.header("설정")
num_games = st.sidebar.number_input("생성할 게임 수", min_value=1, max_value=100, value=5, step=1)

st.sidebar.markdown("### 특정 번호 포함/제외")
include_nums = st.sidebar.multiselect("반드시 포함할 번호 (최대 5개)", list(range(1, 46)))
exclude_nums = st.sidebar.multiselect("제외할 번호", list(range(1, 46)))

if len(include_nums) > 5:
    st.sidebar.error("포함할 번호는 5개까지만 선택할 수 있습니다.")
if set(include_nums) & set(exclude_nums):
    st.sidebar.error("포함할 번호와 제외할 번호에 같은 숫자가 있습니다.")

st.sidebar.markdown("### 예측 규칙 설정")
st.sidebar.caption("적용할 규칙을 선택해주세요. 상세한 설명을 읽고 본인의 전략에 맞게 조합해 보세요.")

if st.sidebar.button("🎲 규칙 무작위 선정", use_container_width=True):
    for rule_name in rules_config.keys():
        st.session_state[f"rule_{rule_name}"] = random.choice([True, False])

selected_rules = []
for rule_name, config in rules_config.items():
    if f"rule_{rule_name}" not in st.session_state:
        st.session_state[f"rule_{rule_name}"] = config["default"]
        
    if st.sidebar.checkbox(rule_name, key=f"rule_{rule_name}"):
        selected_rules.append(rule_name)
    st.sidebar.markdown(f"<p style='font-size: 0.8rem; color: #6c757d; margin-top: -10px; margin-bottom: 15px;'>{config['desc']}</p>", unsafe_allow_html=True)

st.sidebar.markdown("---")'''
content = re.sub(ui_replace_pattern, new_ui_start, content, flags=re.DOTALL)


# Remove the old generate button block and replace with the execution logic since we moved generate_clicked above
old_gen_button_pattern = r'(if st\.sidebar\.button\("번호 생성하기", key="generate_button"\):)'
new_gen_exec = '''if generate_clicked:
    if len(include_nums) > 5 or (set(include_nums) & set(exclude_nums)):
        st.error("포함/제외 번호 설정에 오류가 있습니다. 설정을 확인해주세요.")
    else:'''
content = re.sub(old_gen_button_pattern, new_gen_exec, content)

# Adjust generator call
content = content.replace("predictor.generate_combination(selected_rules)", "predictor.generate_combination(selected_rules, include_nums, exclude_nums)")


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete")
