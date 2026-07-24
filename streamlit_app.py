import re
import streamlit as st
import pandas as pd
import random
import requests
import os
import time
from datetime import datetime, timedelta
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration for UI ---
# Tailwind CSS classes for a distinctive, production-grade look
TAILWIND_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Roboto:wght@400;700&display=swap');
  :root {
    --primary-color: #0056b3; /* Darker Blue for headings */
    --secondary-color: #6c757d; /* Gray */
    --accent-color: #007bff; /* Soft Blue for primary actions */
    --background-color: #f4f6f9; /* Light Background */
    --text-color: #333333; /* Dark Text */
    --card-background: #ffffff; /* White Card */
    --border-color: #dee2e6;
  }
  body {
    font-family: 'Roboto', sans-serif;
    color: var(--text-color);
    background-color: var(--background-color);
  }
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', serif;
    color: var(--primary-color);
    font-weight: 700;
  }
  .stApp {
    background-color: var(--background-color);
    color: var(--text-color);
  }
  .stButton > button {
    background-color: var(--accent-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.375rem;
    font-weight: 700;
    transition: all 0.2s ease-in-out;
  }
  .stButton > button:hover {
    background-color: #0056b3;
    color: white;
    transform: translateY(-2px);
  }
  .stTextInput > div > div > input, .stNumberInput > div > div > input {
    background-color: var(--card-background);
    color: var(--text-color);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
  }
  .stCheckbox > label {
    color: var(--text-color);
    font-weight: bold;
  }
  .stSelectbox > div > div {
    background-color: var(--card-background);
    color: var(--text-color);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
  }
  .stDataFrame {
    color: var(--text-color);
  }
  .card {
    background-color: var(--card-background);
    border-radius: 0.75rem; /* rounded-xl */
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
  .number-circle {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #f1c40f; /* 밝은 노란색/금색 포인트 */
    color: #333333;
    font-weight: 700;
    margin: 0.25rem;
    font-size: 1.1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  .explanation-box {
    background-color: #e9ecef;
    border-left: 4px solid var(--accent-color);
    padding: 1rem;
    margin-top: 1rem;
    border-radius: 0.25rem;
    color: #495057;
  }
</style>
"""
st.markdown(TAILWIND_CSS, unsafe_allow_html=True)

# --- Data Collection (Real API Sync) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE_V2 = os.path.join(script_dir, "lotto_history_v2.csv")

def get_latest_draw_no():
    start_date = datetime(2002, 12, 7, 20, 45)
    now = datetime.now()
    if now < start_date:
        return 1
    diff = now - start_date
    weeks = diff.days // 7
    latest_draw_time = start_date + timedelta(days=weeks * 7)
    if now < latest_draw_time:
        return max(1, weeks)
    return max(1, weeks + 1)

def fetch_lotto_data(draw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    for _ in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                data = res.json()
                if data.get("returnValue") == "success":
                    time.sleep(0.1) # 서버 부하 방지 딜레이
                    return {
                        '회차': data['drwNo'],
                        '번호1': data['drwtNo1'],
                        '번호2': data['drwtNo2'],
                        '번호3': data['drwtNo3'],
                        '번호4': data['drwtNo4'],
                        '번호5': data['drwtNo5'],
                        '번호6': data['drwtNo6'],
                        '보너스': data['bnusNo']
                    }
        except Exception:
            time.sleep(0.5)
            pass
    return None

def init_supabase():
    try:
        if hasattr(st, "secrets") and "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            return {"url": url, "key": key}
    except Exception:
        pass
    return None

def sync_to_supabase(supabase_client, df_or_list):
    """
    Supabase DB에 데이터를 동기화합니다 (REST API 사용).
    """
    import requests
    import streamlit as st
    if not supabase_client: return
    try:
        records = []
        if isinstance(df_or_list, pd.DataFrame):
            for _, row in df_or_list.iterrows():
                records.append({
                    'draw_no': int(row['회차']), 'num1': int(row['번호1']), 'num2': int(row['번호2']),
                    'num3': int(row['번호3']), 'num4': int(row['번호4']), 'num5': int(row['번호5']),
                    'num6': int(row['번호6']), 'bonus': int(row['보너스'])
                })
        else:
            for r in df_or_list:
                records.append({
                    'draw_no': int(r['회차']), 'num1': int(r['번호1']), 'num2': int(r['번호2']),
                    'num3': int(r['번호3']), 'num4': int(r['번호4']), 'num5': int(r['번호5']),
                    'num6': int(r['번호6']), 'bonus': int(r['보너스'])
                })

        headers = {
            "apikey": supabase_client["key"],
            "Authorization": f"Bearer {supabase_client['key']}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        url = f"{supabase_client['url']}/rest/v1/lotto_history"

        for i in range(0, len(records), 500):
            res = requests.post(url, headers=headers, json=records[i:i+500])
            res.raise_for_status()
    except Exception as e:
        st.sidebar.warning(f"Supabase 동기화 오류: {e}")
        print(f"Supabase sync error: {e}")

def get_lotto_data():
    """
    기존 로컬 CSV 파일에서 데이터를 로드하거나, 최신 데이터를 API로 가져옵니다.
    """
    import requests
    df = pd.DataFrame()
    use_supabase = False
    
    # 1. Supabase에서 먼저 데이터 가져오기 시도
    supabase_client = init_supabase()
    if supabase_client:
        try:
            all_data = []
            offset = 0
            limit = 1000
            
            headers = {
                "apikey": supabase_client["key"],
                "Authorization": f"Bearer {supabase_client['key']}"
            }
            
            while True:
                url = f"{supabase_client['url']}/rest/v1/lotto_history?select=*&offset={offset}&limit={limit}"
                res = requests.get(url, headers=headers)
                res.raise_for_status()
                data = res.json()
                if not data:
                    break
                all_data.extend(data)
                if len(data) < limit:
                    break
                offset += limit
                
            if all_data:
                df = pd.DataFrame(all_data)
                df.rename(columns={'draw_no': '회차', 'num1': '번호1', 'num2': '번호2', 'num3': '번호3', 'num4': '번호4', 'num5': '번호5', 'num6': '번호6', 'bonus': '보너스'}, inplace=True)
                use_supabase = True
        except Exception as e:
            st.sidebar.warning(f"Supabase 연결 실패 (로컬 모드로 진행합니다): {e}")
            supabase_client = None

    if not use_supabase and os.path.exists(HISTORY_FILE_V2):
        df = pd.read_csv(HISTORY_FILE_V2)
        if supabase_client and not df.empty:
            sync_to_supabase(supabase_client, df)
            
    latest_draw = get_latest_draw_no()
    saved_draws = set(df['회차'].tolist()) if not df.empty else set()
    all_draws = set(range(1, latest_draw + 1))
    draws_to_fetch = list(all_draws - saved_draws)
    
    if draws_to_fetch:
        total_to_fetch = len(draws_to_fetch)
        progress_text = f"동행복권 누락/최신 당첨 결과 동기화 중... (총 {total_to_fetch}개 회차)"
        progress_bar = st.progress(0, text=progress_text)
        
        new_data = []
        completed = 0
        consecutive_failures = 0
        stop_flag = [False]
        
        def fetch_task(draw_no):
            if stop_flag[0]:
                return None
            return fetch_lotto_data(draw_no)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_draw = {executor.submit(fetch_task, draw): draw for draw in draws_to_fetch}
            for future in concurrent.futures.as_completed(future_to_draw):
                data = future.result()
                if data:
                    new_data.append(data)
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                completed += 1
                
                # 너무 많은 연속 실패 시 (서버 차단 등) 강제 종료
                if consecutive_failures >= 15:
                    stop_flag[0] = True
                    break
                
                # Streamlit 재실행 시 데이터 증발 방지를 위해 50개마다 중간 저장
                if completed % 50 == 0 or completed == total_to_fetch:
                    progress_bar.progress(completed / total_to_fetch, text=f"{progress_text} - 진행중: {completed}/{total_to_fetch} (병렬 처리 중🚀)")
                    if new_data:
                        temp_df = pd.DataFrame(new_data)
                        df = pd.concat([df, temp_df], ignore_index=True)
                        df.drop_duplicates(subset=['회차'], inplace=True)
                        df.sort_values(by='회차', inplace=True)
                        df.to_csv(HISTORY_FILE_V2, index=False)
                        
                        if supabase_client:
                            sync_to_supabase(supabase_client, new_data)
                            
                        new_data = [] # 저장 후 버퍼 비우기

        progress_bar.empty()
        
        # 데이터 업데이트 실패 감지 및 수동 입력 폼 제공
        missing_draws = list(set(range(1, latest_draw + 1)) - set(df['회차'].tolist()))
        if missing_draws:
            st.error(f"🚨 동행복권 서버 응답 지연/차단으로 인해 최신 {len(missing_draws)}개 회차 동기화에 실패했습니다.")
            with st.expander("🛠️ 비상용: 수동으로 최신 회차 입력하기", expanded=True):
                st.info("동행복권 서버 마비 시, 인터넷에서 최신 당첨 번호를 검색하여 직접 입력하시면 즉시 분석기에 반영됩니다.")
                with st.form("manual_input_form"):
                    manual_draw_no = st.number_input("회차 번호", min_value=1, max_value=latest_draw, value=missing_draws[0])
                    cols = st.columns(7)
                    n1 = cols[0].number_input("번호1", min_value=1, max_value=45, value=1)
                    n2 = cols[1].number_input("번호2", min_value=1, max_value=45, value=2)
                    n3 = cols[2].number_input("번호3", min_value=1, max_value=45, value=3)
                    n4 = cols[3].number_input("번호4", min_value=1, max_value=45, value=4)
                    n5 = cols[4].number_input("번호5", min_value=1, max_value=45, value=5)
                    n6 = cols[5].number_input("번호6", min_value=1, max_value=45, value=6)
                    bn = cols[6].number_input("보너스", min_value=1, max_value=45, value=7)
                    
                    if st.form_submit_button("수동 데이터 DB에 저장하기"):
                        nums = [n1, n2, n3, n4, n5, n6]
                        if len(set(nums)) != 6:
                            st.error("당첨 번호 6개는 중복될 수 없습니다.")
                        elif bn in nums:
                            st.error("보너스 번호는 당첨 번호와 중복될 수 없습니다.")
                        else:
                            nums.sort()
                            manual_record = [{
                                '회차': manual_draw_no,
                                '번호1': nums[0], '번호2': nums[1], '번호3': nums[2],
                                '번호4': nums[3], '번호5': nums[4], '번호6': nums[5],
                                '보너스': bn
                            }]
                            temp_df = pd.DataFrame(manual_record)
                            df = pd.concat([df, temp_df], ignore_index=True)
                            df.drop_duplicates(subset=['회차'], inplace=True)
                            df.sort_values(by='회차', inplace=True)
                            df.to_csv(HISTORY_FILE_V2, index=False)
                            if supabase_client:
                                sync_to_supabase(supabase_client, manual_record)
                            st.success(f"{manual_draw_no}회차 데이터가 수동으로 저장되었습니다!")
                            time.sleep(1)
                            st.rerun()
            
    return df

# --- Prediction Rules ---
class LottoPredictor:
    def __init__(self, historical_data):
        self.data = historical_data
        self.all_numbers = [col for col in self.data.columns if '번호' in col]
        
        if not self.data.empty:
            self.winning_numbers_flat = self.data[self.all_numbers].values.flatten()
            self.number_counts = pd.Series(self.winning_numbers_flat).value_counts().sort_index()
            self.freq_sorted_numbers = self.number_counts.sort_values(ascending=False).index.tolist()
            # For "이월수", get last draw
            self.last_draw_numbers = self.data.iloc[-1][self.all_numbers].values.tolist()
            if len(self.data) >= 10:
                last_10_flat = self.data.iloc[-10:][self.all_numbers].values.flatten()
                self.cold_numbers = [n for n in range(1, 46) if n not in last_10_flat]
            else:
                self.cold_numbers = list(range(1, 46))
        else:
            self.freq_sorted_numbers = list(range(1, 46))
            self.last_draw_numbers = []
            self.cold_numbers = list(range(1, 46))

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
        
    def check_filters(self, comb, rules_to_apply, custom_pools=None):
        if custom_pools is None: custom_pools = {}
        if "이웃수 포함 패턴 (Neighbor Numbers)" in rules_to_apply:
            if hasattr(self, 'last_draw_numbers') and self.last_draw_numbers:
                neighbors = set()
                for num in self.last_draw_numbers:
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

        if "쌍수 제한 (Double Digits Limit)" in rules_to_apply:
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
                
        if "끝수 합 구간 필터 (Last Digits Sum 15~35)" in rules_to_apply:
            ld_sum = sum(x % 10 for x in comb)
            if not (15 <= ld_sum <= 35):
                return False, "끝수 합 구간 필터 (Last Digits Sum 15~35)"
                
        if "5의 배수 개수 제한 (Multiples of 5 Limit 0~2)" in rules_to_apply:
            mult5_count = sum(1 for x in comb if x % 5 == 0)
            if mult5_count > 2:
                return False, "5의 배수 개수 제한 (Multiples of 5 Limit 0~2)"
                
        if "[극한] 역대 빈도 상위 15개 번호 한정 (Top 15 Frequent Only)" in rules_to_apply:
            top_15 = custom_pools.get("top_15", set(self.freq_sorted_numbers[:15]))
            if any(x not in top_15 for x in comb):
                return False, "[극한] 역대 빈도 상위 15개 번호 한정 (Top 15 Frequent Only)"
                
        if "[극한] 최근 5회차 완전 제외 (Exclude Last 5 Draws)" in rules_to_apply:
            if hasattr(self, 'data') and not self.data.empty:
                last_5_flat = custom_pools.get("exclude_last_5", set(self.data.iloc[-5:][self.all_numbers].values.flatten()))
                if any(x in last_5_flat for x in comb):
                    return False, "[극한] 최근 5회차 완전 제외 (Exclude Last 5 Draws)"
                    
        if "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)" in rules_to_apply:
            target_cold = custom_pools.get("cold_numbers", self.cold_numbers)
            cold_count = sum(1 for x in comb if x in target_cold)
            if cold_count < 3:
                return False, "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)"
                
        if "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)" in rules_to_apply:
            target_cold = custom_pools.get("exclude_cold_numbers", self.cold_numbers)
            if any(x in target_cold for x in comb):
                return False, "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)"
                
        if "끝수 합 구간 필터 (Last Digits Sum 15~35)" in rules_to_apply:
            ld_sum = sum(x % 10 for x in comb)
            if not (15 <= ld_sum <= 35):
                return False, "끝수 합 구간 필터 (Last Digits Sum 15~35)"
                
        if "5의 배수 개수 제한 (Multiples of 5 Limit 0~2)" in rules_to_apply:
            mult5_count = sum(1 for x in comb if x % 5 == 0)
            if mult5_count > 2:
                return False, "5의 배수 개수 제한 (Multiples of 5 Limit 0~2)"
                
        return True, None

    def calculate_valid_combinations_estimate(self, rules_to_apply, custom_pools=None, n_samples=10000):
        """
        몬테카를로 시뮬레이션을 사용하여 현재 규칙을 통과하는 전체 조합 수를 추정합니다.
        전체 8,145,060 조합을 모두 검사하면 너무 오래 걸리므로, 1만 개를 무작위로 뽑아 비율을 계산합니다.
        """
        if not rules_to_apply:
            return 8145060
            
        pass_count = 0
        pool = list(range(1, 46))
        for _ in range(n_samples):
            test_comb = random.sample(pool, 6)
            test_comb.sort()
            is_valid, _ = self.check_filters(test_comb, rules_to_apply, custom_pools)
            if is_valid:
                pass_count += 1
                
        pass_ratio = pass_count / n_samples
        estimated_total = int(8145060 * pass_ratio)
        return estimated_total

    def generate_combination(self, rules_to_apply, include_nums=None, exclude_nums=None, custom_pools=None):
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
                
                is_valid, _ = self.check_filters(comb, current_rules, custom_pools)
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

    def compare_with_past_results(self, generated_combination):
        if self.data.empty:
            return []
            
        match_results = []
        for index, row in self.data.iterrows():
            past_winning_numbers = sorted([row[f'번호{i}'] for i in range(1, 7)])
            bonus_number = row['보너스']

            matches = len(set(generated_combination) & set(past_winning_numbers))
            
            rank = "낙첨"
            if matches == 6:
                rank = "1등"
            elif matches == 5 and bonus_number in generated_combination:
                rank = "2등"
            elif matches == 5:
                rank = "3등"
            elif matches == 4:
                rank = "4등"
            elif matches == 3:
                rank = "5등"
            
            if matches >= 3: # Only show significant matches
                match_results.append({
                    '회차': row['회차'],
                    '일치 개수': matches,
                    '보너스 일치': 'O' if bonus_number in generated_combination else 'X',
                    '등수': rank,
                    '당첨 번호': ' '.join(map(str, past_winning_numbers)) + f' + {bonus_number}'
                })
        return match_results

# --- Streamlit App ---
st.title("🔮 로또 번호 예측 시스템 (실시간 동기화 & 고수익 전략)")
st.markdown("동행복권의 실제 당첨 데이터를 실시간으로 수집하고, 독자적인 고수익 예측 규칙을 적용하여 번호를 제안합니다.")

# Fetch historical data
historical_df = get_lotto_data()
predictor = LottoPredictor(historical_df)

rules_config = {
        "이웃수 포함 패턴 (Neighbor Numbers)": {
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
    },
    "끝수 합 구간 필터 (Last Digits Sum 15~35)": {
        "desc": "선택된 6개 번호의 맨 끝자리 숫자들의 총합이 15에서 35 사이가 되도록 합니다.",
        "default": True
    },
    "5의 배수 개수 제한 (Multiples of 5 Limit 0~2)": {
        "desc": "5의 배수(5, 10, 15...)가 최대 2개까지만 나오도록 제한합니다.",
        "default": True
    },
    "[극한] 역대 빈도 상위 15개 번호 한정 (Top 15 Frequent Only)": {
        "desc": "역대 가장 많이 당첨된 번호 15개 안에서만 6개를 모두 추출합니다. (조합 수 극강 축소)",
        "default": False
    },
    "[극한] 최근 5회차 완전 제외 (Exclude Last 5 Draws)": {
        "desc": "최근 5번의 추첨에서 나왔던 모든 번호(약 20~25개)를 완전히 배제합니다.",
        "default": False
    },
    "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)": {
        "desc": "최근 10번 동안 한 번도 안 나온 번호들을 무조건 3개 이상 포함시킵니다.",
        "default": False
    },
    "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)": {
        "desc": "최근 10번 동안 한 번도 안 나온 번호들을 이번 회차에서 완전히 배제합니다.",
        "default": False
    }
}



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

st.sidebar.header("설정")
num_games = st.sidebar.number_input("생성할 게임 수", min_value=1, max_value=100, value=5, step=1)

st.sidebar.markdown("### 특정 번호 포함/제외")
include_text = st.sidebar.text_input("반드시 포함할 번호 (콤마나 공백 구분, 최대 5개)", "")
exclude_text = st.sidebar.text_input("제외할 번호 (콤마나 공백 구분)", "")

def parse_numbers(text):
    if not text.strip(): return []
    parts = re.split(r'[,\s]+', text.strip())
    nums = []
    for p in parts:
        if p.isdigit():
            n = int(p)
            if 1 <= n <= 45:
                nums.append(n)
    return list(set(nums))

include_nums = parse_numbers(include_text)
exclude_nums = parse_numbers(exclude_text)

if len(include_nums) > 5:
    st.sidebar.error("포함할 번호는 5개까지만 입력할 수 있습니다.")
if set(include_nums) & set(exclude_nums):
    st.sidebar.error("포함할 번호와 제외할 번호에 중복된 숫자가 있습니다.")

st.sidebar.markdown("### 예측 규칙 설정")
st.sidebar.caption("적용할 규칙을 선택해주세요. 상세한 설명을 읽고 본인의 전략에 맞게 조합해 보세요.")
st.sidebar.info("💡 **안내:** '이월수 포함'과 '직전 완전 제외'는 모순되는 조건이므로 동시에 선택할 수 없습니다. 하나를 선택하면 다른 하나는 자동 해제됩니다.")

def toggle_carryover():
    if st.session_state.get("rule_이월수 포함 필터 (Carryover Number)"):
        st.session_state["rule_직전 회차 완전 제외 (Exclude Recent)"] = False

def toggle_exclude_recent():
    if st.session_state.get("rule_직전 회차 완전 제외 (Exclude Recent)"):
        st.session_state["rule_이월수 포함 필터 (Carryover Number)"] = False
        
def toggle_cold_include():
    if st.session_state.get("rule_[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)"):
        st.session_state["rule_[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)"] = False

def toggle_cold_exclude():
    if st.session_state.get("rule_[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)"):
        st.session_state["rule_[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)"] = False

selected_rules = []

normal_rules = {k: v for k, v in rules_config.items() if not k.startswith("[극한]")}
extreme_rules = {k: v for k, v in rules_config.items() if k.startswith("[극한]")}

for rule_name, config in normal_rules.items():
    if f"rule_{rule_name}" not in st.session_state:
        st.session_state[f"rule_{rule_name}"] = config["default"]
        
    kwargs = {"key": f"rule_{rule_name}"}
    if rule_name == "이월수 포함 필터 (Carryover Number)":
        kwargs["on_change"] = toggle_carryover
    elif rule_name == "직전 회차 완전 제외 (Exclude Recent)":
        kwargs["on_change"] = toggle_exclude_recent
        
    if st.sidebar.checkbox(rule_name, **kwargs):
        selected_rules.append(rule_name)
    st.sidebar.markdown(f"<p style='font-size: 0.8rem; color: #6c757d; margin-top: -10px; margin-bottom: 15px;'>{config['desc']}</p>", unsafe_allow_html=True)

custom_extreme_pools = {}

if extreme_rules:
    st.sidebar.markdown("### ⚠️ 극한 규칙 (조합 대폭 감소)")
    st.sidebar.caption("수백만 개의 조합을 수천 개 수준 이하로 떨어뜨리기 위한 강력한 필터들입니다.")
    for rule_name, config in extreme_rules.items():
        if f"rule_{rule_name}" not in st.session_state:
            st.session_state[f"rule_{rule_name}"] = config["default"]
            
        kwargs = {"key": f"rule_{rule_name}"}
        if rule_name == "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)":
            kwargs["on_change"] = toggle_cold_include
        elif rule_name == "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)":
            kwargs["on_change"] = toggle_cold_exclude
            
        is_checked = st.sidebar.checkbox(rule_name, **kwargs)
        if is_checked:
            selected_rules.append(rule_name)
            
        st.sidebar.markdown(f"<p style='font-size: 0.8rem; color: #d9534f; margin-top: -10px; margin-bottom: 15px;'>{config['desc']}</p>", unsafe_allow_html=True)
        
        with st.sidebar.expander("세부 번호 취사선택", expanded=False):
            if not is_checked:
                st.caption("위의 메인 규칙 체크박스를 먼저 켜주셔야 세부 번호를 선택할 수 있습니다.")
            else:
                pool_nums = []
                state_key_prefix = ""
                if rule_name == "[극한] 역대 빈도 상위 15개 번호 한정 (Top 15 Frequent Only)":
                    pool_nums = sorted(predictor.freq_sorted_numbers[:15])
                    state_key_prefix = "custom_top15_"
                elif rule_name == "[극한] 최근 5회차 완전 제외 (Exclude Last 5 Draws)":
                    if hasattr(predictor, 'data') and not predictor.data.empty:
                        pool_nums = sorted(list(set(predictor.data.iloc[-5:][predictor.all_numbers].values.flatten())))
                    state_key_prefix = "custom_excl5_"
                elif rule_name == "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)":
                    pool_nums = sorted(predictor.cold_numbers)
                    state_key_prefix = "custom_cold_"
                elif rule_name == "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)":
                    pool_nums = sorted(predictor.cold_numbers)
                    state_key_prefix = "custom_excl_cold_all_"
                
                selected_nums_for_rule = set()
                if pool_nums:
                    cols = st.columns(3)
                    for idx, n in enumerate(pool_nums):
                        col = cols[idx % 3]
                        if f"{state_key_prefix}{n}" not in st.session_state:
                            st.session_state[f"{state_key_prefix}{n}"] = True
                        if col.checkbox(str(n), key=f"{state_key_prefix}{n}"):
                            selected_nums_for_rule.add(n)
                            
                if rule_name == "[극한] 역대 빈도 상위 15개 번호 한정 (Top 15 Frequent Only)":
                    custom_extreme_pools["top_15"] = selected_nums_for_rule
                elif rule_name == "[극한] 최근 5회차 완전 제외 (Exclude Last 5 Draws)":
                    custom_extreme_pools["exclude_last_5"] = selected_nums_for_rule
                elif rule_name == "[극한] 장기 미출현 번호 3개 이상 강제 포함 (3+ Cold Numbers)":
                    custom_extreme_pools["cold_numbers"] = selected_nums_for_rule
                elif rule_name == "[극한] 장기 미출현 번호 완전 제외 (Exclude All Cold Numbers)":
                    custom_extreme_pools["exclude_cold_numbers"] = selected_nums_for_rule

st.sidebar.markdown("---")
with st.sidebar.spinner("조합 확률 계산 중..."):
    estimated_total = predictor.calculate_valid_combinations_estimate(selected_rules, custom_pools=custom_extreme_pools)
    ratio = (estimated_total / 8145060) * 100
    st.sidebar.info(f"📊 **현재 규칙 통과 예상 조합 수**\n\n약 **{estimated_total:,}**개 (전체 중 **{ratio:.2f}%**)")

generate_clicked = st.sidebar.button("번호 생성하기", key="generate_button", type="primary", use_container_width=True)
st.sidebar.markdown("---")
random_generate_clicked = st.sidebar.button("🎲 조합별 랜덤 규칙 생성", key="random_generate_button", use_container_width=True)
st.sidebar.caption("위 버튼을 누르면 각 게임마다 적용되는 규칙이 무작위로 선택되어, 다채로운 패턴의 조합을 생성합니다.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🆘 서버 차단 시 백업 플랜")
st.sidebar.caption("서버 접속이 차단된 경우, 동행복권 공식 홈페이지에서 받은 '엑셀 다운로드' 파일을 여기에 올려주시면 데이터가 자동 복구됩니다.")

uploaded_file = st.sidebar.file_uploader("동행복권 엑셀 파일 업로드", type=['xls', 'xlsx', 'csv'])
if uploaded_file is not None:
    if "processed_file" not in st.session_state or st.session_state.processed_file != uploaded_file.name:
        try:
            uploaded_file.seek(0)
            df_parsed = None
            required_cols = ['회차', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스']
            
            if uploaded_file.name.endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file)
                if all(c in temp_df.columns for c in required_cols):
                    df_parsed = temp_df[required_cols]
            else:
                import io
                dfs = []
                try:
                    # 1. 시도: 진짜 엑셀 포맷인지 확인
                    uploaded_file.seek(0)
                    dfs = [pd.read_excel(uploaded_file)]
                except Exception:
                    # 2. 시도: 동행복권 고유의 HTML 위장 엑셀 포맷 처리
                    uploaded_file.seek(0)
                    file_bytes = uploaded_file.read()
                    html_content = ""
                    for enc in ['cp949', 'euc-kr', 'utf-8']:
                        try:
                            html_content = file_bytes.decode(enc)
                            break
                        except UnicodeDecodeError:
                            pass
                    
                    if not html_content.strip():
                        raise ValueError("파일 내용을 읽을 수 없습니다 (빈 파일이거나 지원하지 않는 인코딩).")
                    
                    dfs = pd.read_html(io.StringIO(html_content))
                
                for d in dfs:
                    df_extracted = None
                    
                    # Check if headers are already in columns
                    col_vals = [str(x).strip() for x in d.columns]
                    if '회차' in col_vals and '보너스' in col_vals:
                        df_extracted = d.copy()
                        if '1' not in col_vals and '당첨번호' in col_vals:
                            idx_win = col_vals.index('당첨번호')
                            rename_dict = {}
                            for i in range(6):
                                if idx_win + i < len(df_extracted.columns):
                                    rename_dict[df_extracted.columns[idx_win + i]] = str(i + 1)
                            df_extracted = df_extracted.rename(columns=rename_dict)
                    else:
                        for idx in range(min(10, len(d))):
                            row_vals = [str(x).strip() for x in d.iloc[idx].values]
                            if '회차' in row_vals and '보너스' in row_vals:
                                d.columns = row_vals
                                df_extracted = d.iloc[idx+1:].copy()
                                if '1' not in row_vals and '당첨번호' in row_vals:
                                    idx_win = row_vals.index('당첨번호')
                                    rename_dict = {}
                                    for i in range(6):
                                        if idx_win + i < len(df_extracted.columns):
                                            rename_dict[df_extracted.columns[idx_win + i]] = str(i + 1)
                                    df_extracted = df_extracted.rename(columns=rename_dict)
                                break
                    
                    if df_extracted is not None:
                        col_map = {}
                        for col in df_extracted.columns:
                            col_str = str(col).strip()
                            if col_str == '회차': col_map[col] = '회차'
                            elif col_str == '1': col_map[col] = '번호1'
                            elif col_str == '2': col_map[col] = '번호2'
                            elif col_str == '3': col_map[col] = '번호3'
                            elif col_str == '4': col_map[col] = '번호4'
                            elif col_str == '5': col_map[col] = '번호5'
                            elif col_str == '6': col_map[col] = '번호6'
                            elif col_str == '보너스': col_map[col] = '보너스'
                        
                        df_extracted = df_extracted.rename(columns=col_map)
                        if all(c in df_extracted.columns for c in required_cols):
                            df_parsed = df_extracted[required_cols]
                            break
            
            if df_parsed is not None:
                df_parsed = df_parsed.apply(pd.to_numeric, errors='coerce').dropna()
                
                if os.path.exists(HISTORY_FILE_V2):
                    existing_df = pd.read_csv(HISTORY_FILE_V2)
                    merged_df = pd.concat([existing_df, df_parsed], ignore_index=True)
                else:
                    merged_df = df_parsed
                    
                merged_df.drop_duplicates(subset=['회차'], inplace=True)
                merged_df.sort_values(by='회차', inplace=True)
                merged_df.to_csv(HISTORY_FILE_V2, index=False)
                
                supabase_client = init_supabase()
                if supabase_client:
                    sync_to_supabase(supabase_client, df_parsed)
                
                st.session_state.processed_file = uploaded_file.name
                st.sidebar.success(f"✅ 성공! {len(df_parsed)}개의 데이터를 복구했습니다. 페이지를 새로고침합니다.")
                time.sleep(2)
                st.rerun()
            else:
                st.sidebar.error("파일 형식을 인식할 수 없습니다. 공식 엑셀/CSV 파일을 올려주세요.")
        except Exception as e:
            st.sidebar.error(f"파일 처리 중 오류 발생: {e}")

if not generate_clicked and not random_generate_clicked:
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
            st.subheader("📈 역대 1등 당첨 번호 규칙 적중률 통계")
            st.markdown("1회차부터 최근 회차까지의 모든 당첨 번호들이 각 통계 필터를 얼마나 통과했는지 분석한 결과입니다. **적중률 60% 이상**인 규칙은 좌측 메뉴에서 자동으로 기본 선택됩니다.")
            
            if rule_stats:
                stats_df = pd.DataFrame(list(rule_stats.items()), columns=['규칙', '적중률(%)'])
                stats_df['적중률(%)'] = stats_df['적중률(%)'].round(1)
                stats_df = stats_df.sort_values(by='적중률(%)', ascending=False).set_index('규칙')
                st.bar_chart(stats_df)
                
        else:
            st.error("데이터 동기화에 실패했습니다. 네트워크를 확인해주세요.")

else:
        if len(include_nums) > 5 or (set(include_nums) & set(exclude_nums)):
            st.error("포함/제외 번호 설정에 오류가 있습니다. 설정을 확인해주세요.")
        else:
            st.subheader("생성된 로또 번호 조합")
            generated_combinations = []
            
            with st.spinner("통계적 필터를 적용하여 수만 개의 난수 중 최적의 조합을 추출 중입니다..."):
                for i in range(num_games):
                    if random_generate_clicked:
                        current_game_rules = [r for r in list(rules_config.keys()) if random.choice([True, False])]
                    else:
                        current_game_rules = selected_rules
                        
                    combination, ignored_rules, explanation = predictor.generate_combination(current_game_rules, include_nums, exclude_nums, custom_pools=custom_extreme_pools)
                    
                    if random_generate_clicked:
                        explanation.insert(0, "🎲 **랜덤 규칙 적용**: 이 조합은 무작위로 선택된 규칙 세트를 기반으로 생성되었습니다.")
                        
                    generated_combinations.append((combination, ignored_rules, explanation))
                    
            # Check if any rule was ignored
            all_ignored = set()
            for _, ign, _ in generated_combinations:
                all_ignored.update(ign)
                
            if all_ignored:
                st.warning(f"⚠️ 설정하신 필터 조건이 너무 많거나 상호 충돌하여(예: 이월수 포함 vs 제외) 수학적으로 일치하는 조합을 찾기 어려웠습니다. 정상적인 출력을 위해 다음 조건들이 자동으로 **무시(해제)** 되었습니다:\\n\\n" + "\\n".join([f"- **{r}**" for r in all_ignored]) + "\\n\\n이 조건들을 강제로 반영하고 싶으시다면, 좌측 메뉴에서 다른 필터를 일부 해제하여 조건을 완화한 뒤 다시 생성해주세요.")
                
            # 복사 및 공유 기능 제공
            all_games_text = "🎯 로또 예측 번호\\n\\n"
            for i, (combination, _, _) in enumerate(generated_combinations):
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
            
            for i, (combination, ignored, explanation) in enumerate(generated_combinations):
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"#### 게임 {i+1}", unsafe_allow_html=True)
                num_display = "".join([f"<span class='number-circle'>{num}</span>" for num in combination])
                st.markdown(f"<p>{num_display}</p>", unsafe_allow_html=True)
                
                with st.expander("💡 적용된 필터 규칙 보기"):
                    for exp in explanation:
                        if "해당 필터의 통계적 조건을 완벽하게 통과했습니다." not in exp:
                            st.markdown(exp)
                            
                    st.markdown("<br/>", unsafe_allow_html=True)
                    r_col1, r_col2 = st.columns(2)
                    r_list = list(rules_config.keys())
                    r_half = len(r_list) // 2 + len(r_list) % 2
                    
                    for r_idx, r_name in enumerate(r_list):
                        target_col = r_col1 if r_idx < r_half else r_col2
                        if r_name in ignored:
                            target_col.markdown(f"<span style='color: #d39e00;'>⚠️ {r_name} (무시됨)</span>", unsafe_allow_html=True)
                        else:
                            is_valid, _ = predictor.check_filters(combination, [r_name])
                            if is_valid:
                                target_col.markdown(f"<span style='color: #28a745;'>✅ {r_name}</span>", unsafe_allow_html=True)
                            else:
                                target_col.markdown(f"<span style='color: #dc3545;'>❌ {r_name}</span>", unsafe_allow_html=True)
                
                if ignored:
                    st.markdown(f"<p style='color: #ff4b4b; font-size: 0.85rem; margin-top: 10px;'>※ 수학적 한계로 무시된 조건: {', '.join(ignored)}</p>", unsafe_allow_html=True)
                    
                st.markdown("</div>", unsafe_allow_html=True)
    
            st.subheader("과거 당첨 결과와 비교")
            st.info("생성된 조합이 과거 당첨 번호와 얼마나 일치하는지 시뮬레이션한 결과입니다.")
            
            for i, (combination, _, _) in enumerate(generated_combinations):
                st.markdown(f"### 게임 {i+1} 조합: {', '.join(map(str, combination))}")
                comparison_results = predictor.compare_with_past_results(combination)
                
                if comparison_results:
                    df_results = pd.DataFrame(comparison_results)
                    st.dataframe(df_results.sort_values(by='일치 개수', ascending=False))
                else:
                    st.write("과거 실제 당첨 기록 중 3개 이상 일치하는 결과가 없습니다.")

st.markdown("---")
st.markdown("본 시스템은 통계적 경향성을 분석하여 번호를 제안하지만, 로또 당첨은 전적으로 운에 따릅니다.")
