# 로또 번호 예측기 (Lotto Predictor) 🎱

본 애플리케이션은 과거 로또(6/45) 당첨 데이터를 수집 및 분석하여 통계적 규칙 기반으로 번호 조합을 추천하고, 각 조합의 생성 근거를 설명하는 Streamlit 웹 애플리케이션입니다.

> **면책 조항 (Disclaimer)**
> 로또는 매 회차 독립 시행이므로 과거의 통계가 미래를 보장하지 않습니다. 본 서비스에서 제공하는 "적합도 점수"나 "확률"은 통계적 경향성에 기반한 참고 자료일 뿐, 당첨 확률을 실제로 높이는 것은 아닙니다. 오락 목적으로만 사용하시기 바랍니다.

## 주요 기능 ✨
- **자동 데이터 수집**: 동행복권 공식 API를 통해 역대 로또 당첨 내역을 자동 수집 및 로컬 CSV 캐싱
- **프리미엄 UI 대시보드**: 통계 데이터(빈도, 홀짝, 합계 등)를 인터랙티브 Plotly 차트로 제공
- **규칙 기반 예측 엔진**: 적합도 채점제(Soft Scoring)를 도입하여, 고빈도 번호, 홀짝 비율, 합계 범위 등 다양한 조건의 가중합으로 최적의 조합 추천
- **과거 비교 분석**: 생성된 번호 조합이 과거 1~5등 당첨 이력과 얼마나 유사한지 자동 대조

## 로컬 실행 방법 🚀

### 1. 환경 설정 및 의존성 설치
본 프로젝트는 Python 3.10+ 환경을 권장합니다.

```bash
# 가상 환경 생성 (선택 사항)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 애플리케이션 실행
```bash
streamlit run app.py
```
실행 후 브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

## GitHub 업로드 및 Streamlit Cloud 배포 가이드 ☁️

### GitHub 저장소 업로드
1. GitHub(https://github.com) 에 로그인하여 새로운 Repository를 생성합니다 (예: `lotto-predictor`).
2. 로컬 프로젝트 폴더에서 아래 명령어를 순서대로 실행합니다:
```bash
git init
git add .
git commit -m "Initial commit: 로또 예측기 기본 구조 완성"
git branch -M main
git remote add origin https://github.com/본인계정/lotto-predictor.git
git push -u origin main
```

### Streamlit Cloud 배포
1. Streamlit Community Cloud(https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. `New app` 버튼을 클릭합니다.
3. 배포할 Repository(`본인계정/lotto-predictor`)와 Branch(`main`)를 선택합니다.
4. Main file path에 `app.py`를 입력합니다.
5. `Deploy!` 버튼을 클릭하면 수 분 내에 전 세계 어디서나 접속 가능한 앱 링크가 생성됩니다.

---
**주의**: Streamlit Cloud 환경에서는 캐시 파일(`data/lotto_history.csv`)이 재부팅 시 초기화될 수 있으므로, 주기적으로 크롤링이 발생할 수 있습니다. 이를 방지하려면 GitHub에 최신 `lotto_history.csv`를 함께 커밋하는 것이 좋습니다.
