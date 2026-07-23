import pytest
import pandas as pd
from src.analyzer import LottoAnalyzer
from src.predictor import LottoPredictor
from src.comparator import LottoComparator

@pytest.fixture
def mock_analyzer():
    # 빈 데이터프레임으로 초기화된 Analyzer 모의 객체
    df = pd.DataFrame(columns=["drwNo", "drwNoDate", "num1", "num2", "num3", "num4", "num5", "num6", "bonusNo"])
    return LottoAnalyzer(df)

@pytest.fixture
def predictor(mock_analyzer):
    recent_draw = [1, 2, 3, 4, 5, 6]
    return LottoPredictor(mock_analyzer, recent_draw=recent_draw)

def test_consecutive_count():
    assert LottoAnalyzer.count_consecutive([1, 2, 3, 10, 15, 20]) == 3
    assert LottoAnalyzer.count_consecutive([1, 3, 5, 7, 9, 11]) == 1
    assert LottoAnalyzer.count_consecutive([1, 2, 5, 6, 10, 11]) == 2
    assert LottoAnalyzer.count_consecutive([1, 2, 3, 4, 5, 6]) == 6

def test_ac_value():
    # AC값 = 차이 집합 크기 - 5
    # [1,2,3,4,5,6] -> 차이: 1,2,3,4,5 (총 5개) -> AC = 0
    assert LottoAnalyzer.calculate_ac([1, 2, 3, 4, 5, 6]) == 0
    
def test_evaluation_score(predictor):
    config = {
        "rules": {
            "odd_even": True,
            "sum_range": True,
            "consecutive": True,
            "ac_value": False,
            "band_balance": True,
            "exclude_recent": True
        },
        "weights": {
            "odd_even": 1.0,
            "sum_range": 1.0,
            "consecutive": 1.0,
            "band_balance": 1.0,
            "exclude_recent": 1.0
        }
    }
    
    # 1. 완벽한 밸런스 조합 테스트 (홀짝 3:3, 합계 약 138, 1연속, 번호대 분산, 최근회차 중복없음)
    good_comb = [12, 17, 24, 29, 36, 41]
    score_good, _ = predictor._evaluate_combination(good_comb, config)
    
    # 2. 나쁜 조합 테스트 (직전 회차와 100% 동일 -> 페널티 및 가점 실패)
    bad_comb = [1, 2, 3, 4, 5, 6]
    score_bad, _ = predictor._evaluate_combination(bad_comb, config)
    
    # 좋은 조합이 나쁜 조합보다 점수가 높아야 함
    assert score_good > score_bad

def test_generate_combinations(predictor):
    config = {
        "rules": {"odd_even": True},
        "weights": {"odd_even": 1.0}
    }
    num_games = 3
    results = predictor.generate_combinations(num_games, config)
    
    assert len(results) == num_games
    for res in results:
        assert len(res["numbers"]) == 6
        assert "score" in res
        assert "details" in res

def test_comparator():
    data = {
        "drwNo": [1],
        "drwNoDate": ["2023-01-01"],
        "num1": [10], "num2": [15], "num3": [20], "num4": [25], "num5": [30], "num6": [35],
        "bonusNo": [40]
    }
    df = pd.DataFrame(data)
    comparator = LottoComparator(df)
    
    # 6개 모두 일치 (1등)
    res_1 = comparator.compare_combination([10, 15, 20, 25, 30, 35])
    assert not res_1.empty
    assert res_1.iloc[0]["등수"] == "1등"
    
    # 5개 일치 + 보너스 (2등)
    res_2 = comparator.compare_combination([10, 15, 20, 25, 30, 40])
    assert res_2.iloc[0]["등수"] == "2등"
    
    # 3개 미만 일치 (결과 없음)
    res_fail = comparator.compare_combination([1, 2, 3, 4, 5, 6])
    assert res_fail.empty
