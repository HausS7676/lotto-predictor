import os
import re

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

stats_logic = """
@st.cache_data(ttl=3600)
def calculate_rule_statistics(df, rules_list):
    stats = {rule: 0 for rule in rules_list}
    total_draws = len(df)
    
    if total_draws == 0:
        return stats
        
    temp_predictor = LottoPredictor(pd.DataFrame(columns=df.columns))
    all_numbers_cols = [col for col in df.columns if '번호' in col]
    
    for i in range(1, total_draws):
        prev_row = df.iloc[i-1]
        curr_row = df.iloc[i]
        
        temp_predictor.last_draw_numbers = [int(prev_row[c]) for c in all_numbers_cols]
        if i >= 10:
            last_10_flat = df.iloc[i-10:i][all_numbers_cols].values.flatten()
            temp_predictor.cold_numbers = [n for n in range(1, 46) if n not in last_10_flat]
        else:
            temp_predictor.cold_numbers = list(range(1, 46))
            
        curr_numbers = [int(curr_row[c]) for c in all_numbers_cols]
        
        for rule in rules_list:
            is_valid, _ = temp_predictor.check_filters(curr_numbers, [rule])
            if is_valid:
                stats[rule] += 1
                
    evaluated_draws = total_draws - 1
    if evaluated_draws > 0:
        for rule in stats:
            stats[rule] = (stats[rule] / evaluated_draws) * 100
            
    return stats

rule_stats = calculate_rule_statistics(historical_df, list(rules_config.keys()))

# Update defaults dynamically based on 60% threshold
for rule, stat in rule_stats.items():
    if stat >= 60.0:
        rules_config[rule]["default"] = True
    else:
        rules_config[rule]["default"] = False
"""

content = content.replace('st.sidebar.header("설정")', stats_logic + '\nst.sidebar.header("설정")')

ui_logic = """
        st.subheader("📈 역대 1등 당첨 번호 규칙 적중률 통계")
        st.markdown("1회차부터 최근 회차까지의 모든 당첨 번호들이 각 통계 필터를 얼마나 통과했는지 분석한 결과입니다. **적중률 60% 이상**인 규칙은 좌측 메뉴에서 자동으로 기본 선택됩니다.")
        
        if rule_stats:
            stats_df = pd.DataFrame(list(rule_stats.items()), columns=['규칙', '적중률(%)'])
            stats_df['적중률(%)'] = stats_df['적중률(%)'].round(1)
            stats_df = stats_df.sort_values(by='적중률(%)', ascending=False).set_index('규칙')
            st.bar_chart(stats_df)
"""

ui_insert_target = """                    else:
                        target_col.markdown(f"<span style='color: #dc3545;'>❌ {rule_name}</span>", unsafe_allow_html=True)"""

content = content.replace(ui_insert_target, ui_insert_target + "\n\n" + ui_logic)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update 5 complete")
