import re

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace rules_config
new_rules_config = '''rules_config = {
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
        "desc": "특정 10번대 구간(예: 10~19)에 4개 이상의 번호가 몰리지 않도록 균형을 맞춥니다.",
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
}
'''

content = re.sub(r'rules_config = \{.*?\n\}\n', new_rules_config, content, flags=re.DOTALL)

# 2. Replace LottoPredictor
new_lotto_predictor = '''class LottoPredictor:
    def __init__(self, historical_data):
        self.data = historical_data
        self.all_numbers = [col for col in self.data.columns if '번호' in col]
        
        if not self.data.empty:
            self.winning_numbers_flat = self.data[self.all_numbers].values.flatten()
            self.number_counts = pd.Series(self.winning_numbers_flat).value_counts().sort_index()
            self.freq_sorted_numbers = self.number_counts.sort_values(ascending=False).index.tolist()
            # For "이월수", get last draw
            self.last_draw_numbers = self.data.iloc[-1][self.all_numbers].values.tolist()
        else:
            self.freq_sorted_numbers = list(range(1, 46))
            self.last_draw_numbers = []

    def _generate_candidate_numbers(self):
        """기본 후보 번호 생성 (빈도 기반)"""
        if len(self.freq_sorted_numbers) < 45:
            return random.sample(range(1, 46), 6)
            
        high_freq_pool = self.freq_sorted_numbers[:int(len(self.freq_sorted_numbers) * 0.7)]
        low_freq_pool = self.freq_sorted_numbers[int(len(self.freq_sorted_numbers) * 0.7):]
        
        candidates = []
        if len(high_freq_pool) >= 4:
            candidates.extend(random.sample(high_freq_pool, 4))
        else:
            candidates.extend(high_freq_pool)
            candidates.extend(random.sample(low_freq_pool, 6 - len(candidates)))

        if len(low_freq_pool) >= 2:
            candidates.extend(random.sample(low_freq_pool, 2))
        else:
            candidates.extend(random.sample(high_freq_pool, 6 - len(candidates)))

        return list(set(candidates))

    def get_ac_value(self, comb):
        diffs = set()
        for i in range(len(comb)):
            for j in range(i+1, len(comb)):
                diffs.add(abs(comb[i] - comb[j]))
        return len(diffs) - 5
        
    def check_filters(self, comb, rules_to_apply):
        """Returns (is_valid, failed_rule_name)"""
        if "홀짝 균형 (Odd/Even Balance)" in rules_to_apply:
            odd_count = sum(1 for x in comb if x % 2 != 0)
            if odd_count not in [2, 3, 4]:
                return False, "홀짝 균형 (Odd/Even Balance)"
                
        if "총합 구간 필터 (Sum Range)" in rules_to_apply:
            s = sum(comb)
            if not (100 <= s <= 170):
                return False, "총합 구간 필터 (Sum Range)"
                
        if "연속 번호 제한 (Consecutive Limit)" in rules_to_apply:
            cons = 0
            for i in range(len(comb)-1):
                if comb[i+1] - comb[i] == 1:
                    cons += 1
                    if cons >= 2:
                        return False, "연속 번호 제한 (Consecutive Limit)"
                else:
                    cons = 0
                    
        if "AC값 필터 (Arithmetic Complexity)" in rules_to_apply:
            if self.get_ac_value(comb) < 7:
                return False, "AC값 필터 (Arithmetic Complexity)"
                
        if "번호대 균형 (Band Balance)" in rules_to_apply:
            bands = [x // 10 for x in comb]
            if any(bands.count(b) >= 4 for b in set(bands)):
                return False, "번호대 균형 (Band Balance)"
                
        if "직전 회차 완전 제외 (Exclude Recent)" in rules_to_apply:
            if any(x in self.last_draw_numbers for x in comb):
                return False, "직전 회차 완전 제외 (Exclude Recent)"
                
        if "고저 비율 (High/Low Balance)" in rules_to_apply:
            high_count = sum(1 for x in comb if x >= 23)
            if high_count not in [2, 3, 4]:
                return False, "고저 비율 (High/Low Balance)"
                
        if "끝수 중복 제한 (Last Digit Check)" in rules_to_apply:
            last_digits = [x % 10 for x in comb]
            if any(last_digits.count(d) >= 3 for d in set(last_digits)):
                return False, "끝수 중복 제한 (Last Digit Check)"
                
        if "이월수 포함 필터 (Carryover Number)" in rules_to_apply:
            carry_count = sum(1 for x in comb if x in self.last_draw_numbers)
            if carry_count < 1:
                return False, "이월수 포함 필터 (Carryover Number)"
                
        if "소수/합성수 균형 (Prime/Composite Balance)" in rules_to_apply:
            primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43}
            prime_count = sum(1 for x in comb if x in primes)
            if prime_count == 0 or prime_count > 3:
                return False, "소수/합성수 균형 (Prime/Composite Balance)"
                
        return True, None

    def generate_combination(self, rules_to_apply):
        current_rules = list(rules_to_apply)
        ignored_rules = []
        
        while True:
            tries = 0
            while tries < 5000: # 5천번 시도
                base_numbers = self._generate_candidate_numbers()
                while len(base_numbers) < 6:
                    base_numbers.append(random.choice([n for n in range(1, 46) if n not in base_numbers]))
                comb = sorted(random.sample(base_numbers, 6))
                
                is_valid, _ = self.check_filters(comb, current_rules)
                if is_valid:
                    return comb, ignored_rules
                
                tries += 1
                
            # If we reach here, we failed to find a valid combination 5000 times
            if current_rules:
                dropped = current_rules.pop() # Remove the last rule (can be randomized)
                ignored_rules.append(dropped)
            else:
                return sorted(random.sample(range(1, 46), 6)), ignored_rules

    def compare_with_past_results(self, generated_combination):
'''

content = re.sub(r'class LottoPredictor:.*?(?=    def compare_with_past_results)', new_lotto_predictor, content, flags=re.DOTALL)

# 3. Replace Button logic
new_button_logic = '''if st.sidebar.button("번호 생성하기", key="generate_button"):
    st.subheader("생성된 로또 번호 조합")
    generated_combinations = []
    
    with st.spinner("통계적 필터를 적용하여 수만 개의 난수 중 최적의 조합을 추출 중입니다..."):
        for i in range(num_games):
            combination, ignored_rules = predictor.generate_combination(selected_rules)
            generated_combinations.append((combination, ignored_rules))
            
    # Check if any rule was ignored
    all_ignored = set()
    for _, ign in generated_combinations:
        all_ignored.update(ign)
        
    if all_ignored:
        st.warning(f"⚠️ 설정하신 필터 조건이 너무 많거나 상호 충돌하여(예: 이월수 포함 vs 제외) 수학적으로 일치하는 조합을 찾기 어려웠습니다. 정상적인 출력을 위해 다음 조건들이 자동으로 **무시(해제)** 되었습니다:\\n\\n" + "\\n".join([f"- **{r}**" for r in all_ignored]) + "\\n\\n이 조건들을 강제로 반영하고 싶으시다면, 좌측 메뉴에서 다른 필터를 일부 해제하여 조건을 완화한 뒤 다시 생성해주세요.")
        
    # 복사 및 공유 기능 제공
    all_games_text = "🎯 로또 예측 번호\\n\\n"
    for i, (combination, _) in enumerate(generated_combinations):
        num_str = ", ".join(map(str, combination))
        all_games_text += f"[게임 {i+1}] {num_str}\\n"
    
    st.markdown("### 📋 전체 번호 복사 및 공유")
    st.caption("우측 상단의 복사 아이콘을 클릭하여 번호를 복사하거나, 아래 버튼을 눌러 지인에게 문자로 공유하세요.")
    st.code(all_games_text, language="text")
    
    import urllib.parse
    encoded_text = urllib.parse.quote(all_games_text)
    sms_url = f"sms:?body={encoded_text}"
    st.markdown(f"""
    <a href="{sms_url}" style="text-decoration: none;">
        <div style="display: inline-block; background-color: #28a745; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; text-align: center; cursor: pointer; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            💬 모바일에서 문자로 공유하기 (무료)
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    for i, (combination, ignored) in enumerate(generated_combinations):
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"#### 게임 {i+1}", unsafe_allow_html=True)
        num_display = "".join([f"<span class='number-circle'>{num}</span>" for num in combination])
        st.markdown(f"<p>{num_display}</p>", unsafe_allow_html=True)
        
        if ignored:
            st.markdown(f"<p style='color: #ff4b4b; font-size: 0.85rem; margin-top: 10px;'>※ 무시된 조건: {', '.join(ignored)}</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("과거 당첨 결과와 비교")
'''

content = re.sub(r'if st.sidebar.button\("번호 생성하기", key="generate_button"\):.*?(?=    st.subheader\("과거 당첨 결과와 비교"\))', new_button_logic, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated lotto_predictor_v2.py successfully")
