import os

# Streamlit 앱 실행 시 lotto_predictor_v2.py를 로드하여 실행합니다.
target_file = os.path.join(os.path.dirname(__file__), "lotto_predictor_v2.py")
with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()
exec(code, globals())
