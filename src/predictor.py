"""
예측 규칙 엔진 (predictor.py)
적합도 스코어링(Soft Scoring) 기반으로 조건에 맞는 최적의 로또 번호를 추천합니다.
"""

import random
from typing import List, Dict, Tuple
from src.analyzer import LottoAnalyzer

class LottoPredictor:
    def __init__(self, analyzer: LottoAnalyzer, recent_draw: list[int] = None):
        self.analyzer = analyzer
        self.recent_draw = recent_draw if recent_draw else []
        
    def generate_combinations(self, num_games: int, config: Dict) -> List[Dict]:
        """
        주어진 수만큼의 번호 조합을 생성하여 점수가 높은 순으로 정렬하여 반환합니다.
        무한 루프 방지를 위해 최대 10,000개의 랜덤 조합을 평가합니다.
        """
        max_attempts = 10000
        evaluated = []
        
        # 중복 없는 무작위 조합을 1만개 생성 후 평가 (몬테카를로 방식)
        for _ in range(max_attempts):
            comb = tuple(sorted(random.sample(range(1, 46), 6)))
            score, details = self._evaluate_combination(list(comb), config)
            evaluated.append({
                "numbers": list(comb),
                "score": score,
                "details": details
            })
            
        # 중복 조합 제거
        unique_evaluated = {tuple(x["numbers"]): x for x in evaluated}.values()
        
        # 점수 내림차순 정렬 후 최상위 num_games 반환
        sorted_combinations = sorted(unique_evaluated, key=lambda x: x["score"], reverse=True)
        return sorted_combinations[:num_games]

    def _evaluate_combination(self, comb: list[int], config: Dict) -> Tuple[float, List[str]]:
        """
        단일 조합의 적합도 점수와 적용된 규칙 설명을 계산합니다.
        """
        score = 0.0
        details = []
        
        rules = config.get("rules", {})
        weights = config.get("weights", {})
        
        # 1. 홀짝 균형 (3:3, 2:4, 4:2 가 가장 이상적)
        if rules.get("odd_even", True):
            odds = sum(1 for x in comb if x % 2 != 0)
            if odds in [2, 3, 4]:
                w = weights.get("odd_even", 1.0)
                score += 20 * w
                details.append("홀짝 비율이 통계적 최빈 구간(2:4~4:2)에 부합합니다.")
                
        # 2. 합계 범위 (100 ~ 175)
        if rules.get("sum_range", True):
            s = sum(comb)
            if 100 <= s <= 175:
                w = weights.get("sum_range", 1.0)
                score += 20 * w
                details.append(f"총합({s})이 역대 최빈 구간(100~175)에 포함됩니다.")
                
        # 3. 연속 번호 (3연속 이상 배제)
        if rules.get("consecutive", True):
            cons = LottoAnalyzer.count_consecutive(comb)
            if cons <= 2:
                w = weights.get("consecutive", 1.0)
                score += 20 * w
                details.append("3개 이상의 연속 번호가 없습니다.")
            elif cons > 2:
                # 3연속 이상이면 페널티
                score -= 10
                
        # 4. AC값 (산술적 복잡도 7 이상)
        if rules.get("ac_value", True):
            ac = LottoAnalyzer.calculate_ac(comb)
            if ac >= 7:
                w = weights.get("ac_value", 1.0)
                score += 15 * w
                details.append(f"산술적 복잡도(AC값 {ac})가 이상적인 수치입니다.")
                
        # 5. 번호대 균형 (특정 10단위 구간에 4개 이상 몰리지 않음)
        if rules.get("band_balance", True):
            bands = [0] * 5
            for n in comb:
                idx = (n - 1) // 10
                if idx > 4: idx = 4
                bands[idx] += 1
                
            if max(bands) <= 3:
                w = weights.get("band_balance", 1.0)
                score += 15 * w
                details.append("특정 번호대(10단위)에 편중되지 않고 고르게 분포되었습니다.")
                
        # 6. 직전 회차 중복 배제 (최근 회차와 2개 이하 일치)
        if rules.get("exclude_recent", True) and self.recent_draw:
            overlap = len(set(comb) & set(self.recent_draw))
            if overlap <= 1:
                w = weights.get("exclude_recent", 1.0)
                score += 10 * w
                details.append(f"직전 당첨 번호와 중복이 적습니다 ({overlap}개 일치).")

        return score, details
