import os

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update check_filters
new_filters = """
        if "이웃수 포함 패턴 (Neighbor Numbers)" in rules_to_apply:
            if hasattr(self, 'latest_winning_numbers') and self.latest_winning_numbers:
                neighbors = set()
                for num in self.latest_winning_numbers:
                    if num > 1: neighbors.add(num - 1)
                    if num < 45: neighbors.add(num + 1)
                neighbor_count = sum(1 for x in comb if x in neighbors)
                if not (1 <= neighbor_count <= 2):
                    return False, "이웃수 포함 패턴 (Neighbor Numbers)"
                    
        if "동형수 쌍 제한 (Mirror Number Limit)" in rules_to_apply:
            mirror_pairs = [(12, 21), (13, 31), (14, 41), (23, 32), (24, 42), (34, 43)]
            pair_count = sum(1 for a, b in mirror_pairs if a in comb and b in comb)
            if pair_count >= 2:
                return False, "동형수 쌍 제한 (Mirror Number Limit)"
                
        if "모서리 패턴 밸런스 (Edge Pattern)" in rules_to_apply:
            edge_numbers = {1, 2, 6, 7, 8, 9, 13, 14, 29, 30, 34, 35, 36, 37, 41, 42}
            edge_count = sum(1 for x in comb if x in edge_numbers)
            if not (1 <= edge_count <= 4):
                return False, "모서리 패턴 밸런스 (Edge Pattern)"
"""

content = content.replace(
    'if "쌍수 제한 (Double Digits Limit)" in rules_to_apply:',
    new_filters.lstrip('\n') + '\n        if "쌍수 제한 (Double Digits Limit)" in rules_to_apply:'
)

# 2. Update rules_config
new_rules = """    "이웃수 포함 패턴 (Neighbor Numbers)": {
        "desc": "직전 회차 당첨 번호의 양옆 숫자(±1)가 1~2개 포함되도록 균형을 맞춥니다.",
        "default": True
    },
    "동형수 쌍 제한 (Mirror Number Limit)": {
        "desc": "12-21, 34-43 등 뒤집었을 때 대칭이 되는 번호쌍이 2쌍 이상 몰리지 않게 제한합니다.",
        "default": True
    },
    "모서리 패턴 밸런스 (Edge Pattern)": {
        "desc": "로또 용지 네 모서리에 위치한 16개 번호가 1~4개만 적절히 들어가도록 조절합니다.",
        "default": True
    },
"""

content = content.replace(
    '"쌍수 제한 (Double Digits Limit)": {',
    new_rules + '    "쌍수 제한 (Double Digits Limit)": {'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update 4 complete")
