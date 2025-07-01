
# PMark2 AI Assistant

설비관리 시스템을 위한 자연어 기반 AI 작업요청 생성 어시스턴트

## 📋 프로젝트 개요

PMark2은 사용자의 자연어 입력을 분석하여 설비관리 시스템의 작업요청을 자동으로 생성하는 AI 어시스턴트입니다. OpenAI GPT-4o를 활용하여 한국어-영어 혼용 표현, 오타, 띄어쓰기 오류 등도 정확하게 이해하고 표준화된 작업요청을 생성합니다.

### 주요 기능
- **자연어 입력 파싱**: 사용자의 자연어 입력을 구조화된 데이터로 변환
- **LLM 기반 용어 정규화**: 다양한 표현을 표준 용어로 정규화
- **유사 작업 추천**: 기존 작업 이력을 기반으로 유사한 작업 추천
- **작업상세 자동 생성**: LLM을 활용한 작업명과 상세 자동 생성
- **최종 작업요청 완성**: 완성된 작업요청을 시스템에 등록

## 🏗️ 시스템 아키텍처

### 전체 구조
```
PMark2-Dev/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── models.py        # 데이터 모델 정의
│   │   ├── config.py        # 설정 관리
│   │   ├── database.py      # 데이터베이스 관리
│   │   ├── agents/
│   │   │   └── parser.py    # 입력 파서
│   │   ├── logic/
│   │   │   ├── normalizer.py # LLM 정규화 엔진
│   │   │   └── recommender.py # 추천 엔진
│   │   └── api/
│   │       ├── chat.py      # 채팅 API
│   │       └── work_details.py # 작업상세 API
│   └── main.py              # FastAPI 앱 진입점
├── frontend/                # React 프론트엔드
└── docs/                    # 문서
```

### 핵심 컴포넌트

#### 1. 입력 파서 (InputParser)
- **파일**: `backend/app/agents/parser.py`
- **담당자**: AI/ML 엔지니어, 백엔드 개발자
- **기능**: 
  - 사용자 입력의 시나리오 판단 (S1: 자연어 요청, S2: ITEMNO 요청)
  - LLM을 활용한 정보 추출 (위치, 설비유형, 현상코드, 우선순위)
  - 추출된 용어의 LLM 정규화
- **수정 가이드**:
  - 새로운 시나리오 추가 시 `_determine_scenario()` 수정
  - 추출 필드 변경 시 `_create_scenario_1_prompt()` 수정
  - 정규화 로직은 `logic/normalizer.py`와 연동

#### 2. LLM 정규화 엔진 (LLMNormalizer)
- **파일**: `backend/app/logic/normalizer.py`
- **담당자**: AI/ML 엔지니어
- **기능**:
  - 자연어 입력을 표준 용어로 정규화
  - 한국어-영어 혼용 표현, 오타, 띄어쓰기 오류 처리
  - 신뢰도 점수 기반 정규화 품질 제어
- **수정 가이드**:
  - `standard_terms` 사전은 실제 DB 데이터와 일치해야 함
  - 새로운 카테고리 추가 시 `standard_terms`에 추가
  - 프롬프트 수정으로 정규화 품질 향상 가능

#### 3. 추천 엔진 (RecommendationEngine)
- **파일**: `backend/app/logic/recommender.py`
- **담당자**: AI/ML 엔지니어, 백엔드 개발자
- **기능**:
  - 파싱된 입력을 기반으로 유사한 작업 검색
  - 유사도 점수 계산 및 정렬
  - LLM을 활용한 작업명/상세 자동 생성
- **수정 가이드**:
  - 추천 알고리즘 개선 시 `get_recommendations()` 수정
  - 유사도 점수 임계값 조정으로 추천 품질 제어
  - 새로운 추천 기준 추가 가능

#### 4. 데이터베이스 관리 (DatabaseManager)
- **파일**: `backend/app/database.py`
- **담당자**: 백엔드 개발자, 데이터베이스 관리자
- **기능**:
  - SQLite 데이터베이스 관리
  - 유사한 알림 데이터 검색
  - LLM 정규화 엔진과 연동한 정확한 매칭
- **수정 가이드**:
  - DB 스키마 변경 시 `_init_database()` 수정
  - 새로운 검색 조건 추가 시 `search_similar_notifications()` 수정
  - 성능 최적화를 위해 인덱스 추가 고려

#### 5. 채팅 API (Chat API)
- **파일**: `backend/app/api/chat.py`
- **담당자**: 백엔드 개발자, API 개발자
- **기능**:
  - 사용자 입력 처리 및 파싱
  - 시나리오별 응답 생성
  - 추천 목록 제공
- **수정 가이드**:
  - 새로운 시나리오 추가 시 `_handle_scenario()` 수정
  - 응답 메시지 형식 변경 시 `_create_response_message()` 수정
  - 에러 처리 로직 개선 가능

#### 6. 작업상세 API (Work Details API)
- **파일**: `backend/app/api/work_details.py`
- **담당자**: 백엔드 개발자, API 개발자
- **기능**:
  - 선택된 추천 항목에 대한 작업상세 생성
  - 최종 작업요청 완성 및 저장
- **수정 가이드**:
  - LLM 프롬프트 수정으로 생성 품질 향상 가능
  - 외부 시스템 연동 로직 추가 필요
  - 트랜잭션 처리 및 롤백 로직 구현 필요

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.8+
- Node.js 16+
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

# 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 프론트엔드 설정

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

### 3. 전체 시스템 실행

```bash
# 프로젝트 루트에서
python scripts/start_backend.py
python scripts/start_frontend.py
```

## 📊 API 문서

### 주요 엔드포인트

#### 1. 채팅 API
- **POST** `/api/v1/chat`
- **기능**: 사용자 입력 분석 및 추천 목록 생성
- **요청**: `ChatRequest` (message, conversation_history)
- **응답**: `ChatResponse` (message, recommendations, parsed_input)

#### 2. 작업상세 생성 API
- **POST** `/api/v1/generate-work-details`
- **기능**: 선택된 추천 항목에 대한 작업상세 생성
- **요청**: `WorkDetailsRequest` (selected_recommendation, user_message)
- **응답**: `WorkDetailsResponse` (work_title, work_details)

#### 3. 작업요청 완성 API
- **POST** `/api/v1/finalize-work-order`
- **기능**: 최종 작업요청 완성 및 저장
- **요청**: `FinalizeRequest` (work_title, work_details, selected_recommendation)
- **응답**: `FinalizeResponse` (message, work_order)

### API 테스트

```bash
# Swagger UI 접속
http://localhost:8000/docs

# curl 예시
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "1PE 압력베젤 고장"}'
```

## 🔧 개발 가이드

### 코드 수정 시 주의사항

#### 1. 모델 변경 시
- `models.py`의 모델 변경 시 API 스키마가 자동으로 업데이트됨
- 새로운 필드 추가 시 기본값 설정 권장
- `Recommendation` 모델의 `priority` 필드는 필수 (finalize-work-order API에서 사용)

#### 2. LLM 프롬프트 수정 시
- 일관성 있는 응답을 위해 `temperature`를 낮게 유지 (0.1~0.3)
- 예시는 실제 사용 사례를 반영하여 업데이트
- JSON 응답 형식 유지

#### 3. 데이터베이스 스키마 변경 시
- 기존 데이터 마이그레이션 필요
- 인덱스 설정으로 성능 최적화
- 외래키 제약조건 추가 시 주의

#### 4. API 응답 형식 변경 시
- Frontend와의 호환성 확인
- 에러 처리는 사용자 친화적으로 구현
- 로깅을 통한 디버깅 지원

### 성능 최적화

#### 1. 캐싱
- LLM 응답 캐싱으로 API 비용 절약
- 데이터베이스 쿼리 결과 캐싱
- 추천 결과 캐싱

#### 2. 배치 처리
- 대량의 용어 정규화 시 배치 처리
- 데이터베이스 쿼리 최적화
- 비동기 처리 활용

#### 3. 모니터링
- API 응답 시간 모니터링
- LLM API 사용량 추적
- 에러율 모니터링

## 🧪 테스트

### 단위 테스트
```bash
# 백엔드 테스트
cd backend
python -m pytest tests/

# 프론트엔드 테스트
cd frontend
npm test
```

### 통합 테스트
```bash
# API 테스트
python scripts/test_api.py

# 전체 시스템 테스트
python scripts/test_system.py
```

### 테스트 시나리오
1. **자연어 입력 테스트**: "1PE 압력베젤 고장" → 정확한 파싱 및 추천
2. **오타 처리 테스트**: "압력베젤" → "Pressure Vessel" 정규화
3. **ITEMNO 조회 테스트**: "ITEMNO 12345" → 특정 작업 정보 제공
4. **작업상세 생성 테스트**: 선택된 추천 항목으로 작업상세 생성
5. **최종 완성 테스트**: 작업요청 완성 및 저장

## 📈 향후 개발 계획

### 단기 계획 (1-2개월)
- [ ] 외부 시스템 연동 (Kafka, ERP 시스템)
- [ ] 사용자 인증 및 권한 관리
- [ ] 작업요청 이력 관리
- [ ] 모바일 앱 개발

### 중기 계획 (3-6개월)
- [ ] 다국어 지원 (영어, 중국어)
- [ ] 음성 입력 지원
- [ ] 이미지 기반 설비 인식
- [ ] 예측 분석 기능

### 장기 계획 (6개월 이상)
- [ ] 머신러닝 모델 도입
- [ ] 실시간 모니터링 대시보드
- [ ] 자동화된 작업 스케줄링
- [ ] AI 기반 예방 정비

## 🤝 팀 협업 가이드

### 코드 리뷰 체크리스트
- [ ] 기능 요구사항 충족
- [ ] 코드 품질 및 가독성
- [ ] 에러 처리 및 예외 상황
- [ ] 성능 최적화
- [ ] 보안 고려사항
- [ ] 테스트 코드 작성

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

## 📞 문의 및 지원

### 담당자 연락처
- **프로젝트 매니저**: [이메일]
- **백엔드 개발**: [이메일]
- **프론트엔드 개발**: [이메일]
- **AI/ML 엔지니어**: [이메일]

### 이슈 리포트
- GitHub Issues를 통한 버그 리포트
- 기능 요청 및 개선 제안
- 기술 지원 요청

## 📄 라이선스

이 프로젝트는 [라이선스명] 하에 배포됩니다.

---

**PMark2 AI Assistant** - 설비관리 시스템의 미래를 만들어갑니다.

# PMark2-Dev

