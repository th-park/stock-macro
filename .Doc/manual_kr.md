# 주식 자동매매 및 백테스팅 시스템 설명서

## 1. 개요
이 프로젝트는 미국 주식의 분단위 캔들 데이터를 수집하여 데이터베이스에 적재하고, 이를 기반으로 모멘텀 전략 등의 알고리즘 트레이딩 전략을 백테스팅하며, 최종적으로 미래에셋증권 API를 통해 실전 자동매매를 수행하는 것을 목표로 합니다.

## 2. 시스템 구조
시스템은 크게 세 가지 주요 모듈로 구성됩니다.

### 2.1 데이터 수집기 (Data Collector)
- **위치**: `app/data_collector.py`
- **역할**: Yahoo Finance (`yfinance`) API를 통해 미국 주식(AAPL, TSLA 등)의 1분봉 데이터를 수집합니다.
- **특징**: 
    - 한 번 실행 시 최근 **7일간**의 데이터를 가져옵니다.
    - 기존 데이터와 비교하여 **중복을 제외하고 일괄 저장(Bulk Insert)**하여 속도가 빠르고 데이터가 누적됩니다.
    - `run_collector.sh` 스크립트를 통해 가상환경 설정과 함께 쉽게 실행할 수 있습니다.

### 2.2 데이터베이스 (Database)
- **위치**: `app/database.py`, `app/models/stock_data.py`
- **기술**: SQLite, SQLAlchemy (ORM)
- **스키마**: `stock_data` 테이블
    - `ticker`: 종목 코드 (예: AAPL)
    - `timestamp`: 시간 (분 단위)
    - `open`, `high`, `low`, `close`, `volume`: OHLCV 데이터
    - `id`: Primary Key

### 2.3 백테스팅 엔진 (Backtester)
- **위치**: `app/backtester/engine.py`, `app/backtester/strategy.py`
- **기술**: `Backtrader` 라이브러리 활용
- **역할**:
    - DB에 저장된 과거 데이터를 로드하여 시뮬레이션을 수행합니다.
    - 매수/매도 로직(현재는 이동평균 돌파 전략)을 검증하고 수익률을 계산합니다.
    - 초기 자본금, 수수료, 슬리피지 등을 설정할 수 있습니다.

## 3. 프로젝트 파일 구성
```
stock-macro/
├── app/
│   ├── __init__.py
│   ├── config.py           # 환경 설정 (API Key, DB 경로 등)
│   ├── database.py         # DB 연결 및 세션 관리 (SessionLocal 사용)
│   ├── dashboard.py        # Streamlit 대시보드 (차트 시각화)
│   ├── data_collector.py   # 데이터 수집 스크립트 (최적화됨)
│   ├── models/             # DB 모델 정의
│   │   ├── __init__.py
│   │   └── stock_data.py
│   └── backtester/         # 백테스팅 모듈
│       ├── __init__.py
│       ├── engine.py       # 백테스트 실행 엔진
│       └── strategy.py     # 매매 전략(알고리즘) 구현
├── main.py                 # DB 초기화 및 메인 진입점
├── check_db.py             # DB 데이터 통계 확인 유틸리티
├── run_collector.sh        # 데이터 수집 실행 쉘 스크립트
├── run_dashboard.sh        # 대시보드 실행 쉘 스크립트
├── requirements.txt        # 파이썬 의존성 패키지 목록
└── .env                    # 환경 변수 (비밀키 등)
```

## 4. 설치 및 실행 방법

### 4.1 환경 설정
1. 파이썬 가상환경 생성 및 활성화
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. 의존성 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```
3. 데이터베이스 초기화
   ```bash
   python main.py
   ```

### 4.2 데이터 수집 실행
Yahoo Finance에서 최근 7일치 1분봉 데이터를 가져와 DB에 축적합니다. 자주 실행하면 데이터가 끊김 없이 이어집니다.
```bash
./run_collector.sh
```
또는 파이썬 직접 실행: `python -m app.data_collector`

### 4.3 데이터 시각화 (대시보드) 실행
수집된 데이터를 웹 브라우저에서 캔들 차트로 확인합니다.
- **특징**: 
    - 일자별 세로 구분선(붉은 점선) 표시
    - 장 종료/주말 등 빈 시간대(Gap) 숨김 처리
    - `Use Container Width` 등 최신 Streamlit 호환성 패치 적용됨
```bash
./run_dashboard.sh
```
접속 주소: `http://localhost:8501` (포트는 자동 할당됨)

### 4.4 데이터베이스 확인 (유틸리티)
DB에 저장된 데이터의 종목별 개수와 기간을 터미널에서 빠르게 확인합니다.
```bash
python check_db.py
```

### 4.5 백테스팅 실행
저장된 데이터를 기반으로 전략을 테스트합니다.
```bash
python -m app.backtester.engine
```

## 5. 향후 계획 (To-Do)
- 미래에셋증권 API 연동 (실전 매매 및 잔고 조회)
- 전략 고도화 (RSI, Bollinger Bands 등 지표 추가)
- 텔레그램 알림 봇 연동
