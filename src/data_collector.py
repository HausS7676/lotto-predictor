"""
로또 당첨 데이터 수집 모듈 (data_collector.py)
동행복권 API를 통해 과거 로또 당첨 번호를 수집하고 CSV로 로컬에 캐싱합니다.
"""

import os
import requests
import pandas as pd
import time
from datetime import datetime
import streamlit as st

# 동행복권 API URL
LOTTO_API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
# 데이터 저장 경로
script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(script_dir, "..", "data", "lotto_history.csv")

def get_latest_draw_no() -> int:
    """
    현재 날짜 기준으로 예상되는 최신 로또 회차를 계산합니다.
    1회차 추첨일: 2002년 12월 7일
    """
    first_draw_date = datetime(2002, 12, 7)
    today = datetime.now()
    delta = today - first_draw_date
    expected_draw = (delta.days // 7) + 1
    
    # 혹시 모를 오차를 위해 현재 예상 회차부터 실제 데이터가 있는지 확인(순차 탐색)
    latest_draw = expected_draw
    while True:
        try:
            res = requests.get(LOTTO_API_URL.format(latest_draw), timeout=5)
            data = res.json()
            if data.get("returnValue") == "success":
                # 현재 회차가 최신인지 확인하기 위해 다음 회차도 확인
                next_res = requests.get(LOTTO_API_URL.format(latest_draw + 1), timeout=5)
                next_data = next_res.json()
                if next_data.get("returnValue") == "fail":
                    return latest_draw
                latest_draw += 1
            else:
                # 미래의 회차를 예측했다면 과거로 내려감
                latest_draw -= 1
                if latest_draw < 1:
                    return 1
        except requests.exceptions.RequestException:
            # 네트워크 에러 시 계산값 중 최소값으로 리턴
            return expected_draw - 1


def fetch_draw_data(draw_no: int, retries: int = 3) -> dict | None:
    """
    특정 회차의 당첨 번호를 가져옵니다. 네트워크 오류 시 재시도합니다.
    """
    for _ in range(retries):
        try:
            response = requests.get(LOTTO_API_URL.format(draw_no), timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("returnValue") == "success":
                return {
                    "drwNo": data["drwNo"],
                    "drwNoDate": data["drwNoDate"],
                    "num1": data["drwtNo1"],
                    "num2": data["drwtNo2"],
                    "num3": data["drwtNo3"],
                    "num4": data["drwtNo4"],
                    "num5": data["drwtNo5"],
                    "num6": data["drwtNo6"],
                    "bonusNo": data["bnusNo"],
                }
            return None
        except requests.exceptions.RequestException:
            time.sleep(1) # 잠시 대기 후 재시도
    return None


def update_lotto_data(progress_callback=None) -> pd.DataFrame:
    """
    로컬 CSV 캐시를 읽어오고, 누락된 최신 회차 데이터를 동행복권 API로부터 받아 업데이트합니다.
    """
    os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
    
    if os.path.exists(DATA_FILE_PATH):
        df = pd.read_csv(DATA_FILE_PATH)
        last_saved_draw = int(df["drwNo"].max()) if not df.empty else 0
    else:
        df = pd.DataFrame(columns=["drwNo", "drwNoDate", "num1", "num2", "num3", "num4", "num5", "num6", "bonusNo"])
        last_saved_draw = 0
        
    latest_draw = get_latest_draw_no()
    
    if last_saved_draw < latest_draw:
        new_records = []
        total_to_fetch = latest_draw - last_saved_draw
        
        for i, draw_no in enumerate(range(last_saved_draw + 1, latest_draw + 1)):
            record = fetch_draw_data(draw_no)
            if record:
                new_records.append(record)
            else:
                # 연속 실패 시 무한 지연(API 차단)을 막기 위해 루프 중단
                if progress_callback:
                    progress_callback(total_to_fetch, total_to_fetch) # 강제 완료 표기
                break
            
            # 진행상황 콜백 (UI 업데이트용)
            if progress_callback:
                progress_callback(i + 1, total_to_fetch)
                
            time.sleep(0.1) # API 차단 방지 딜레이
            
        if new_records:
            new_df = pd.DataFrame(new_records)
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(DATA_FILE_PATH, index=False)
            
    return df
