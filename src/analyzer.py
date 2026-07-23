"""
통계 분석 모듈 (analyzer.py)
과거 로또 당첨 데이터를 기반으로 번호별 출현 빈도, 홀짝 비율, 합계 분포 등 
다양한 통계 지표를 계산합니다.
"""

import pandas as pd
import numpy as np
import streamlit as st
from collections import Counter
from itertools import combinations

class LottoAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        # 1~6번째 당첨 번호만 추출한 numpy 배열 (보너스 번호 제외)
        if not df.empty:
            self.num_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
            self.draws_array = df[self.num_cols].values
        else:
            self.draws_array = np.array([])

    @st.cache_data
    def get_frequency(_self, recent_n: int = None) -> pd.Series:
        """
        번호별 출현 빈도를 계산합니다.
        recent_n이 주어지면 최근 n회차 데이터만 분석합니다.
        """
        if _self.df.empty:
            return pd.Series(dtype=int)
            
        data = _self.draws_array
        if recent_n is not None and recent_n > 0:
            data = data[-recent_n:]
            
        # 1차원 배열로 평탄화 후 빈도 계산
        flat_data = data.flatten()
        counts = pd.Series(flat_data).value_counts().sort_index()
        
        # 1~45 중 안 나온 번호는 0으로 채움
        full_index = pd.Index(range(1, 46))
        return counts.reindex(full_index, fill_value=0)

    @st.cache_data
    def get_last_appearance(_self) -> pd.Series:
        """
        각 번호(1~45)의 가장 마지막 출현 이후 경과된 회차(미출현 기간)를 계산합니다.
        """
        if _self.df.empty:
            return pd.Series(dtype=int)
            
        last_appearance = {}
        total_draws = len(_self.df)
        
        # 최신 회차부터 역순으로 탐색
        for i, row in enumerate(reversed(_self.draws_array)):
            draw_idx = total_draws - i
            for num in row:
                if num not in last_appearance:
                    last_appearance[num] = i # 현재로부터 i회차 전에 출현 (0이면 방금 회차)
            if len(last_appearance) == 45:
                break
                
        # 아직 한 번도 안 나온 번호 처리 (이론상 로또에선 없지만 엣지케이스)
        series = pd.Series(last_appearance)
        full_index = pd.Index(range(1, 46))
        series = series.reindex(full_index, fill_value=total_draws)
        return series

    @st.cache_data
    def get_odd_even_distribution(_self) -> pd.Series:
        """
        역대 당첨 조합의 홀짝 비율 분포를 계산합니다.
        예: "3:3" (홀수 3개, 짝수 3개)
        """
        if _self.df.empty:
            return pd.Series(dtype=int)
            
        odds_count = np.sum(_self.draws_array % 2 != 0, axis=1)
        ratios = [f"{odd}:{6-odd}" for odd in odds_count] # 홀:짝
        return pd.Series(ratios).value_counts()

    @st.cache_data
    def get_sum_distribution(_self) -> dict:
        """
        번호 6개 합계의 분포와 통계치(평균, 표준편차)를 반환합니다.
        """
        if _self.df.empty:
            return {"mean": 0, "std": 0, "sums": pd.Series(dtype=int)}
            
        sums = np.sum(_self.draws_array, axis=1)
        return {
            "mean": np.mean(sums),
            "std": np.std(sums),
            "sums": pd.Series(sums)
        }

    @st.cache_data
    def get_number_band_distribution(_self) -> pd.Series:
        """
        번호대별(1-10, 11-20, ...) 출현 횟수를 계산합니다.
        """
        if _self.df.empty:
            return pd.Series(dtype=int)
            
        flat_data = _self.draws_array.flatten()
        bins = [0, 10, 20, 30, 40, 45]
        labels = ["1-10", "11-20", "21-30", "31-40", "41-45"]
        cats = pd.cut(flat_data, bins=bins, labels=labels)
        return cats.value_counts().reindex(labels)

    @staticmethod
    def calculate_ac(numbers: list[int]) -> int:
        """
        6개 번호의 AC(Arithmetic Complexity, 산술적 복잡도) 값을 계산합니다.
        모든 두 수의 차이(15개) 중 고유한 값의 개수 - 5
        """
        if len(numbers) != 6:
            return 0
        diffs = set()
        for a, b in combinations(numbers, 2):
            diffs.add(abs(a - b))
        return len(diffs) - 5
        
    @staticmethod
    def count_consecutive(numbers: list[int]) -> int:
        """
        주어진 조합에서 가장 길게 연속된 번호의 길이를 반환합니다.
        (예: 1,2,3 -> 3연속)
        """
        nums = sorted(numbers)
        max_cons = 1
        current_cons = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                current_cons += 1
                max_cons = max(max_cons, current_cons)
            else:
                current_cons = 1
        return max_cons
