# PMark2 AI Assistant

설비관리 시스템을 위한 자연어 기반 AI 작업요청 생성 어시스턴트

## 📋 프로젝트 개요

PMark2는 사용자의 자연어 입력을 분석하여 설비관리 시스템의 작업요청을 자동으로 생성하는 AI 어시스턴트입니다. OpenAI GPT-4o를 활용하여 한국어-영어 혼용 표현, 오타, 띄어쓰기 오류 등도 정확하게 이해하고 표준화된 작업요청을 생성합니다.

### 🎯 주요 기능
- **자연어 입력 파싱**: 사용자의 자연어 입력을 구조화된 데이터로 변환
- **LLM 기반 용어 정규화**: 다양한 표현을 표준 용어로 정규화
- **위치 기반 검색**: 위치(Location) 정보를 우선적으로 활용한 정확한 추천
- **유사도 기반 추천**: 개선된 유사도 알고리즘으로 정확한 작업 추천
- **실시간 유사도 표시**: 추천 결과의 유사도를 퍼센트와 색상으로 표시
- **편집 가능한 ITEMNO**: 사용자가 추천 결과의 ITEMNO를 직접 수정 가능

### 🚀 핵심 개선사항 (PMark2)
- **위치 기반 검색 강화**: 위치 정보를 우선적으로 활용하여 더 정확한 추천
- **개선된 유사도 계산**: Levenshtein 거리 기반의 정확한 유사도 점수
- **동적 정규화**: DB의 실제 데이터를 기반으로 한 동적 용어 정규화
- **향상된 UI/UX**: 유사도 점수 시각화, 편집 가능한 필드, 직관적인 인터페이스

## 🏗️ 시스템 아키텍처

### 전체 구조
```
PMark2-Dev/
├── backend/                 # FastAPI 백엔드 (포트 8001)
│   ├── app/
│   │   ├── models.py        # 데이터 모델 정의
│   │   ├── config.py        # 설정 관리
│   │   ├── database.py      # 데이터베이스 관리 (위치 기반 검색 강화)
│   │   ├── agents/
│   │   │   └── parser.py    # 입력 파서 (위치 우선 추출)
│   │   ├── logic/
│   │   │   ├── normalizer.py # LLM 정규화 엔진 (동적 정규화)
│   │   │   └── recommender.py # 추천 엔진 (개선된 유사도)
│   │   └── api/
│   │       ├── chat.py      # 채팅 API
│   │       └── work_details.py # 작업상세 API
│   ├── run.py               # 백엔드 서버 실행 스크립트
│   └── main.py              # FastAPI 앱 진입점
├── chatbot.html             # 메인 프론트엔드 (포트 3001)
├── start_frontend.py        # 프론트엔드 서버 실행 스크립트
├── scripts/                 # 실행 스크립트
└── docs/                    # 문서
```

### 핵심 컴포넌트

#### 1. 입력 파서 (InputParser) - 위치 우선 추출
- **파일**: `backend/app/agents/parser.py`
- **담당자**: AI/ML 엔지니어, 백엔드 개발자
- **기능**: 
  - 사용자 입력의 시나리오 판단 (S1: 자연어 요청, S2: ITEMNO 요청)
  - **위치 정보 우선 추출**: 위치/공정 정보를 가장 중요한 필드로 인식
  - LLM을 활용한 정보 추출 (위치, 설비유형, 현상코드, 우선순위)
  - 추출된 용어의 LLM 정규화
- **수정 가이드**:
  - 새로운 시나리오 추가 시 `_determine_scenario()` 수정
  - 위치 추출 로직 개선 시 `_create_scenario_1_prompt()` 수정
  - 정규화 로직은 `logic/normalizer.py`와 연동

#### 2. LLM 정규화 엔진 (LLMNormalizer) - 동적 정규화
- **파일**: `backend/app/logic/normalizer.py`
- **담당자**: AI/ML 엔지니어
- **기능**:
  - **동적 용어 로딩**: DB의 실제 데이터를 기반으로 표준 용어 동적 로딩
  - 자연어 입력을 표준 용어로 정규화
  - 한국어-영어 혼용 표현, 오타, 띄어쓰기 오류 처리
  - 신뢰도 점수 기반 정규화 품질 제어
- **수정 가이드**:
  - `load_standard_terms_from_db()` 함수로 DB 연동
  - 새로운 카테고리 추가 시 DB 테이블에 추가
  - 프롬프트 수정으로 정규화 품질 향상 가능

#### 3. 추천 엔진 (RecommendationEngine) - 개선된 유사도
- **파일**: `backend/app/logic/recommender.py`
- **담당자**: AI/ML 엔지니어, 백엔드 개발자
- **기능**:
  - **개선된 유사도 계산**: Levenshtein 거리 기반 정확한 유사도 점수
  - **위치 기반 정렬**: 위치 매칭을 우선적으로 고려한 추천
  - 파싱된 입력을 기반으로 유사한 작업 검색
  - 유사도 점수 계산 및 정렬 (임계값 0.2로 조정)
  - LLM을 활용한 작업명/상세 자동 생성
- **수정 가이드**:
  - 유사도 알고리즘 개선 시 `_calculate_enhanced_string_similarity()` 수정
  - 가중치 조정으로 특정 필드 중요도 변경 가능
  - 임계값 조정으로 추천 품질 제어

#### 4. 데이터베이스 관리 (DatabaseManager) - 위치 기반 검색
- **파일**: `backend/app/database.py`
- **담당자**: 백엔드 개발자, 데이터베이스 관리자
- **기능**:
  - SQLite 데이터베이스 관리
  - **위치 기반 검색 강화**: 위치가 입력된 경우 위치 기반 정렬 우선 적용
  - 유사한 알림 데이터 검색
  - LLM 정규화 엔진과 연동한 정확한 매칭
  - **동적 용어 제공**: 정규화 엔진에 실제 DB 용어 제공
- **수정 가이드**:
  - DB 스키마 변경 시 `_init_database()` 수정
  - 위치 기반 검색 로직 개선 시 `search_similar_notifications()` 수정
  - 성능 최적화를 위해 인덱스 추가 고려

#### 5. 채팅 API (Chat API) - 위치 강조
- **파일**: `backend/app/api/chat.py`
- **담당자**: 백엔드 개발자, API 개발자
- **기능**:
  - 사용자 입력 처리 및 파싱
  - **위치 정보 강조**: 위치 입력 안내 및 누락 시 우선 안내
  - 시나리오별 응답 생성
  - 추천 목록 제공
- **수정 가이드**:
  - 새로운 시나리오 추가 시 `_handle_scenario()` 수정
  - 위치 안내 메시지 수정 시 `_create_response_message()` 수정
  - 에러 처리 로직 개선 가능

#### 6. 프론트엔드 (chatbot.html) - 개선된 UI/UX
- **파일**: `chatbot.html`
- **담당자**: 프론트엔드 개발자, UI/UX 디자이너
- **기능**:
  - **개선된 표시 필드**: 위치, 설비유형, 현상코드, 우선순위 표시
  - **유사도 시각화**: 퍼센트 표시 및 색상 구분 (높음/중간/낮음)
  - **편집 가능한 ITEMNO**: 사용자가 직접 수정 가능
  - **반응형 디자인**: 다양한 디바이스 지원
- **수정 가이드**:
  - UI 개선 시 CSS 스타일 수정
  - 새로운 필드 추가 시 `createRecommendationElement()` 수정
  - 유사도 표시 로직은 `scorePercent` 계산 부분 수정

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.8+
- OpenAI API 키

### 1. 백엔드 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp ../env.example .env
# .env 파일에서 OpenAI API 키 설정

# 데이터베이스 초기화
python -c "from app.database import db_manager; db_manager.load_sample_data()"

# 서버 실행 (자동 포트 할당)
python run.py
```

### 2. 프론트엔드 설정

```bash
# 프로젝트 루트에서
python start_frontend.py
```

### 3. 전체 시스템 실행

```bash
# 백엔드 실행 (새 터미널)
cd backend && source venv/bin/activate && python run.py

# 프론트엔드 실행 (새 터미널)
python start_frontend.py
```

### 4. 접속 정보
- **백엔드**: http://localhost:8001 (자동 포트 할당)
- **프론트엔드**: http://localhost:3001 (자동 포트 할당)
- **API 문서**: http://localhost:8001/docs

## 📊 API 문서

### 주요 엔드포인트

#### 1. 채팅 API
- **POST** `/api/v1/chat`
- **기능**: 사용자 입력 분석 및 추천 목록 생성 (위치 기반)
- **요청**: `ChatRequest` (message, conversation_history)
- **응답**: `ChatResponse` (message, recommendations, parsed_input)

#### 2. 작업상세 생성 API
- **POST** `/api/v1/generate-work-details`
- **기능**: 선택된 추천 항목에 대한 작업상세 생성
- **요청**: `WorkDetailsRequest` (selected_recommendation, user_message)
- **응답**: `WorkDetailsResponse` (work_title, work_details)

### API 테스트

```bash
# Swagger UI 접속
http://localhost:8001/docs

# curl 예시 - 위치 기반 검색
curl -X POST "http://localhost:8001/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "No.1 PE 압력베젤 고장"}'

# curl 예시 - 다른 위치
curl -X POST "http://localhost:8001/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "석유제품배합/저장 탱크 누설"}'
```

## 🔧 개발 가이드

### 코드 수정 시 주의사항

#### 1. 위치 기반 검색 관련
- 위치 정보는 가장 중요한 필드로 처리
- `database.py`의 `search_similar_notifications()`에서 위치 우선 정렬
- `parser.py`에서 위치 추출 로직 우선 적용

#### 2. 유사도 계산 관련
- `recommender.py`의 `_calculate_enhanced_string_similarity()` 함수
- 가중치: 설비유형(35%), 위치(35%), 현상코드(20%), 우선순위(10%)
- 임계값 0.2로 설정하여 더 많은 추천 제공

#### 3. 동적 정규화 관련
- `normalizer.py`의 `load_standard_terms_from_db()` 함수
- DB의 실제 데이터를 기반으로 표준 용어 로딩
- 새로운 용어 추가 시 DB 테이블에 추가

#### 4. 프론트엔드 UI 관련
- `chatbot.html`의 `createRecommendationElement()` 함수
- 유사도 점수 표시: 높음(80%+)=녹색, 중간(60-79%)=주황, 낮음(<60%)=빨강
- ITEMNO 편집 기능: `contenteditable` 속성 활용

### 성능 최적화

#### 1. 위치 기반 검색 최적화
- 위치 인덱스 추가로 검색 성능 향상
- 위치 매칭 우선 처리로 정확도 향상

#### 2. 유사도 계산 최적화
- Levenshtein 거리 계산 캐싱
- 배치 처리로 대량 데이터 처리 성능 향상

#### 3. 동적 정규화 최적화
- DB 용어 캐싱으로 반복 쿼리 최소화
- 정규화 결과 캐싱으로 API 비용 절약

## 🧪 테스트

### 테스트 시나리오
1. **위치 기반 검색 테스트**: "No.1 PE 압력베젤 고장" → 정확한 위치 매칭
2. **유사도 계산 테스트**: 다양한 입력에 대한 정확한 유사도 점수
3. **동적 정규화 테스트**: DB 용어와의 정확한 매칭
4. **UI/UX 테스트**: 유사도 표시, ITEMNO 편집 기능

### curl 테스트 예시
```bash
# 위치 기반 검색 테스트
curl -X POST "http://localhost:8001/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "RFCC 펌프 작동불량 일반작업"}'

# ITEMNO 조회 테스트
curl -X POST "http://localhost:8001/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "ITEMNO PE-SE1304B"}'
```

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 빌드 프로세스 또는 보조 도구 변경
```

### 브랜치 전략
- `main`: 프로덕션 배포용
- `develop`: 개발 통합용
- `feature/기능명`: 새로운 기능 개발
- `hotfix/버그명`: 긴급 버그 수정


---

**PMark2 AI Assistant** - 그냥 한 번 만들어봤습니다. 주로 커서가 만들었지만. 참고로만 보아주세요 (To. 종훈 주임님)/ 모듈별 실험용 쥬피터 노트북 파일은 만들고 있습니다. (To. 팀원 여러분 - 수연, 준성)

# PMark2-Dev

