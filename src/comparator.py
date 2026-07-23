"""
비교 분석 모듈 (comparator.py)
생성된 예측 번호를 역대 당첨 데이터와 대조하여,
과거에 이 번호로 몇 등을 할 수 있었는지 시뮬레이션합니다.
"""

import pandas as pd
import numpy as np

class LottoComparator:
    def __init__(self, history_df: pd.DataFrame):
        self.history_df = history_df
        if not history_df.empty:
            self.draws = history_df[["drwNo", "drwNoDate", "num1", "num2", "num3", "num4", "num5", "num6"]].values
            self.bonuses = history_df["bonusNo"].values
        else:
            self.draws = np.array([])
            self.bonuses = np.array([])

    def compare_combination(self, comb: list[int]) -> pd.DataFrame:
        """
        특정 번호 조합(6개)을 전체 역대 회차와 대조합니다.
        3개 이상 일치(5등 이상)한 내역만 DataFrame으로 반환합니다.
        """
        if self.history_df.empty:
            return pd.DataFrame()

        comb_set = set(comb)
        results = []

        for i, row in enumerate(self.draws):
            draw_no = row[0]
            draw_date = row[1]
            winning_nums = set(row[2:8])
            bonus_num = self.bonuses[i]
            
            match_count = len(comb_set & winning_nums)
            bonus_match = bonus_num in comb_set
            
            # 3개 미만 일치면 꽝
            if match_count < 3:
                continue
                
            rank = self._calculate_rank(match_count, bonus_match)
            
            results.append({
                "회차": draw_no,
                "추첨일": draw_date,
                "일치 번호 수": match_count,
                "보너스 일치": "O" if bonus_match else "X",
                "등수": rank
            })
            
        df = pd.DataFrame(results)
        if not df.empty:
            # 상위 등수가 먼저 오도록 정렬
            df = df.sort_values(by=["등수", "회차"], ascending=[True, False]).reset_index(drop=True)
            
        return df

    def _calculate_rank(self, match_count: int, bonus_match: bool) -> str:
        """
        일치 개수와 보너스 일치 여부에 따른 등수를 반환합니다.
        """
        if match_count == 6:
            return "1등"
        elif match_count == 5 and bonus_match:
            return "2등"
        elif match_count == 5:
            return "3등"
        elif match_count == 4:
            return "4등"
        elif match_count == 3:
            return "5등"
        else:
            return "낙첨"

    def get_best_record_summary(self, comb: list[int]) -> str:
        """
        해당 조합의 가장 높았던 과거 등수를 요약 문자열로 반환합니다.
        """
        df = self.compare_combination(comb)
        if df.empty:
            return "과거 당첨 이력(5등 이상) 없음"
            
        best_rank = df.iloc[0]["등수"]
        rank_counts = df["등수"].value_counts().to_dict()
        
        summary_parts = []
        for rank in ["1등", "2등", "3등", "4등", "5등"]:
            if rank in rank_counts:
                summary_parts.append(f"{rank} {rank_counts[rank]}회")
                
        return f"최고 기록: {best_rank} ({', '.join(summary_parts)})"
