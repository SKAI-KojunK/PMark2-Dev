# PMark1 - 대화형 작업요청 챗봇 시스템

PMark1은 공정 관리 및 작업요청을 지원하는 AI 기반 대화형 챗봇 시스템입니다.

## 🆕 새로운 기능 (대화형 챗봇)

### ✨ 주요 특징
- **멀티턴 대화**: 자연스러운 대화형 인터페이스
- **스마트 분석**: 공정명, 위치, 설비, 상태 4가지 항목 자동 추출
- **실시간 완전성 게이지**: 타이핑 중 7-segment 게이지로 정보 충실도 표시
- **인텔리전트 추천**: 부족한 정보를 AI가 추정하여 추천 제공
- **편집 가능한 선택지**: 추천 결과를 사용자가 수정/편집 가능
- **AI 작업명/상세 생성**: 선택된 추천으로 작업명과 상세내용 자동 생성
- **다단계 작업 완성**: 추천 선택 → AI 생성 → 사용자 편집 → 최종 확정
- **네트워크 접속 지원**: 동료들과 공유 가능한 네트워크 접속
- **멀티 사용자 동시 접속**: 여러 명이 동시에 사용 가능

### 🎯 작동 방식
1. **정보 입력**: 사용자가 자연어로 작업 관련 정보 입력
2. **실시간 분석**: 타이핑 중 7-segment 게이지로 완전성 표시
3. **AI 분석**: 4가지 핵심 항목(공정명, 위치, 설비, 상태) 자동 추출
4. **완전성 판단**:
   - 4개 항목 모두 있음: 즉시 추천 제공
   - 3개 항목: 빠진 항목 추정하여 추천 제공
   - 2개 이하: 추가 정보 요청
5. **추천 선택**: 동그라미 버튼으로 선택, 내용 편집 가능
6. **"작성완료"**: AI가 작업명과 작업상세를 생성
7. **편집 및 확정**: 사용자가 내용 수정 후 "확정" 버튼으로 최종 완성

## 🚀 빠른 시작

### 1. 백엔드 서버 시작
```bash
cd backend
python run.py
```
**출력 예시:**
```
🚀 PMark1 Backend Server Starting...
🌐 Server running on:
   • Local:    http://localhost:5001
   • Network:  http://192.168.0.60:5001
📡 Other computers can access: http://192.168.0.60:5001
```

### 2. 프론트엔드 서버 시작
```bash
python start_frontend.py
```
**출력 예시:**
```
🚀 PMark1 Frontend Server Starting...
📁 Current directory: /Users/YMARX/Dropbox/2025_ECMiner/C_P02_SKAI/03_진행/PMark1
🌐 Server running on:
   • Local:    http://localhost:3000
   • Network:  http://192.168.0.60:3000
📡 Other computers can access:
   • Chatbot:     http://192.168.0.60:3000/
   • Prototype:   http://192.168.0.60:3000/old
👥 Multi-user support: ✅ ENABLED
🛑 Press Ctrl+C to stop the server
✅ chatbot.html found
🔥 Server ready for multiple concurrent users!
```

### 3. 접속 방법

#### 🏠 로컬 접속 (본인만 사용)
- **대화형 챗봇**: http://localhost:3000/
- **기존 프로토타입**: http://localhost:3000/old

#### 🌐 네트워크 접속 (동료와 공유)
- **대화형 챗봇**: http://192.168.0.60:3000/
- **기존 프로토타입**: http://192.168.0.60:3000/old

> 💡 **동료 접속 방법**: 같은 WiFi(라우터)를 사용하는 동료에게 네트워크 URL을 공유하면 바로 접속 가능합니다.

## ⚙️ 서버 관리

### 🛑 서버 중지 방법
**백엔드와 프론트엔드 서버 모두 동일한 방법으로 중지할 수 있습니다:**

#### 단축키로 중지
```bash
Ctrl + C  # 서버가 실행 중인 터미널에서 입력
```

#### 프로세스 강제 종료
```bash
# 백엔드 서버 중지
pkill -f "run.py"

# 프론트엔드 서버 중지  
pkill -f "start_frontend.py"

# 모든 PMark1 관련 프로세스 중지
pkill -f "PMark1"
```

#### 포트 기반 프로세스 확인 및 종료
```bash
# 사용 중인 포트 확인
lsof -ti:3000  # 프론트엔드 포트
lsof -ti:5001  # 백엔드 포트

# 특정 포트 사용 프로세스 종료
kill $(lsof -ti:3000)  # 프론트엔드 종료
kill $(lsof -ti:5001)  # 백엔드 종료
```

### 🔄 서버 재시작
```bash
# 1단계: 기존 서버 중지
pkill -f "run.py"
pkill -f "start_frontend.py"

# 2단계: 새로 시작
cd backend && python run.py &
python start_frontend.py &
```

### 📊 서버 상태 확인
```bash
# 프로세스 확인
ps aux | grep -E "(run.py|start_frontend.py)"

# 포트 사용 상태 확인
netstat -an | grep LISTEN | grep -E ":300[0-9]|:500[0-9]"

# 서버 응답 테스트
curl -s http://localhost:5001/ && echo "✅ 백엔드 정상"
curl -s http://localhost:3000/ | head -1 && echo "✅ 프론트엔드 정상"
```

## 🌐 네트워크 설정 및 공유

### 📡 네트워크 접속 지원
- **자동 IP 감지**: 시스템이 현재 네트워크 IP를 자동으로 감지
- **0.0.0.0 바인딩**: 모든 네트워크 인터페이스에서 접속 허용
- **포트 충돌 방지**: 자동으로 사용 가능한 포트 할당
- **멀티 사용자 지원**: ThreadingTCPServer로 동시 다중 접속 처리
- **스레드 안전성**: 각 사용자별 독립적인 스레드에서 처리

### 👥 동료와 공유하기
1. **같은 WiFi 연결**: 동료가 같은 라우터(WiFi)에 연결되어 있어야 함
2. **IP 주소 확인**: 서버 시작 시 표시되는 Network URL 확인
3. **URL 공유**: `http://192.168.0.60:3000/` 형태의 URL을 동료에게 공유
4. **즉시 접속**: 동료가 해당 URL로 바로 접속 가능
5. **동시 사용**: 여러 명이 동시에 접속하여 각자 작업 요청 가능

> ⚡ **동시 접속**: 최대 **수십 명**이 동시에 접속 가능하며, 각 사용자는 **독립적인 세션**을 가집니다.

### 🔧 네트워크 문제 해결
```bash
# 현재 IP 주소 확인
ifconfig | grep "inet " | grep -v 127.0.0.1

# 포트 사용 상태 확인
netstat -an | grep LISTEN | grep -E ":300[0-9]|:500[0-9]"

# 서버 연결 테스트
curl http://localhost:3000/
curl http://192.168.0.60:3000/
```

## 🏗️ 시스템 구조

### 백엔드 (FastAPI)
```
backend/
├── main.py          # 메인 API 서버 (채팅, 추천, 작업생성)
├── run.py           # 서버 시작 스크립트 (네트워크 지원)
├── requirements.txt # Python 의존성
└── .env             # 환경 변수 설정 (OpenAI API Key)
```

### 프론트엔드
```
chatbot.html              # 새로운 대화형 챗봇 UI (7-segment 게이지)
frontend-prototype.html   # 기존 프로토타입 UI
start_frontend.py         # 프론트엔드 서버 (네트워크 지원)
```

## 📋 API 엔드포인트

### 🆕 대화형 챗봇 API

#### POST `/chat`
```json
{
  "message": "생산 1팀에서 2RFCC Air Pump가 파손되었습니다",
  "conversation_history": []
}
```

**응답 예시:**
```json
{
  "message": "모든 정보가 충분합니다! 다음과 같은 추천 결과를 준비했습니다.",
  "field_analysis": {
    "process": "생산 1팀",
    "location": "2RFCC", 
    "equipment": "Air Pump",
    "status": "파손",
    "confidence_score": 0.9,
    "missing_fields": []
  },
  "recommendations": [...],
  "response_type": "provide_recommendations",
  "completeness_gauge": 1.0
}
```

#### POST `/generate-work-details`
선택된 추천으로 AI가 작업명과 작업상세를 생성합니다.
```json
{
  "selected_recommendation": {
    "itemno": "EG-AD-001",
    "process": "생산 1팀",
    "location": "2RFCC",
    "equipType": "Air Pump", 
    "statusCode": "파손",
    "score": 95
  },
  "user_message": "생산 1팀에서 2RFCC Air Pump가 파손되었습니다"
}
```

**응답 예시:**
```json
{
  "work_title": "생산1팀 2RFCC Air Pump 파손 수리",
  "work_details": "생산 1팀 2RFCC 지역의 Air Pump에서 파손이 발생하여 긴급 수리가 필요합니다. 파손 부위 점검 및 교체 부품 확인 후 수리 작업을 진행해주시기 바랍니다."
}
```

#### POST `/finalize-work-order`
최종 작업요청을 완성합니다.
```json
{
  "work_title": "생산1팀 2RFCC Air Pump 파손 수리",
  "work_details": "수정된 작업 상세 내용...",
  "selected_recommendation": {...},
  "user_message": "원본 사용자 입력"
}
```

### 📊 기존 API (호환성 유지)

#### POST `/analyze`
텍스트 분석

#### POST `/recommend`  
추천 결과 생성

#### GET `/test-openai`
OpenAI 연결 테스트

#### GET `/`
헬스 체크

## 🔧 설정

### 환경 변수 (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 지원 모델
- OpenAI GPT-4o

### 시스템 요구사항
- **Python**: 3.13.3+
- **macOS**: 24.5.0+ (개발 환경)
- **네트워크**: 동일 라우터/WiFi 환경 (팀 공유 시)

## 💡 사용 예시

### 완전한 정보 입력
```
사용자: "생산 1팀에서 2RFCC Air Pump가 파손되었습니다"
게이지: 🟢🟢🟢🟢🟢🟢🟢 (100% - 초록색)
챗봇: "모든 정보가 충분합니다! 추천 결과를 준비했습니다."
→ 즉시 5개 추천 제공
```

### 부분 정보 입력
```
사용자: "생산 1팀에서 Air Pump 문제"  
게이지: 🟡🟡🟡🟡⬜⬜⬜ (60% - 노란색)
챗봇: "위치 정보가 빠져있지만 추정해서 추천을 드리겠습니다."
→ 위치를 추정한 추천 제공
```

### 정보 부족
```
사용자: "뭔가 문제가 있어요"
게이지: 🟠🟠⬜⬜⬜⬜⬜ (20% - 주황색)
챗봇: "보다 정확한 안내를 위해 추가 정보를 입력해주세요."
→ 필요한 항목들 안내
```

### 작업 완성 프로세스
```
1. 추천 선택 → "작성완료" 클릭
2. AI가 작업명/상세 자동 생성
3. 사용자가 내용 수정/편집
4. "확정" 클릭 → 최종 작업요청 완성
```

## 🎨 UI 특징

### 7-Segment 실시간 완전성 게이지
- **0-30%**: 🟠 주황색 (정보 부족)
- **30-70%**: 🟡 노란색 (보통)  
- **70-100%**: 🟢 초록색 (충분)
- **실시간 동작**: 타이핑 중 즉시 반영

### 좌우 분할 레이아웃
- **왼쪽**: 스크롤 가능한 대화창
- **오른쪽**: 추천 결과 및 편집 영역
- **하단**: 예시 문장, 입력창, 완전성 게이지

### 추천 선택지
- 동그라미 선택 버튼
- 실시간 편집 가능한 입력 필드
- 호버 효과 및 선택 상태 표시
- 점수별 색상 구분

### 작업 편집 인터페이스
- 작업명 입력 필드
- 작업상세 텍스트 영역
- 실시간 편집 가능
- 최종 확정 버튼

## 🔍 문제해결

### 네트워크 접속 문제
1. **같은 WiFi 확인**: 모든 사용자가 동일한 라우터에 연결되어 있는지 확인
2. **방화벽 설정**: macOS 방화벽에서 Python 접속 허용
3. **IP 주소 변경**: 라우터 재시작 시 IP가 변경될 수 있음

```bash
# 현재 IP 주소 다시 확인
ifconfig | grep "inet " | grep -v 127.0.0.1

# 서버 재시작
pkill -f "run.py"
pkill -f "start_frontend.py"
cd backend && python run.py &
python start_frontend.py &
```

### 포트 충돌
시스템이 자동으로 사용 가능한 포트를 찾습니다:
- **백엔드**: 5001-5010
- **프론트엔드**: 3000-3009

### 백엔드 서버 검색 실패
프론트엔드가 백엔드를 찾지 못하는 경우:
1. 브라우저 콘솔(F12)에서 연결 시도 확인
2. 백엔드 서버가 먼저 실행되어 있는지 확인
3. 2초 타임아웃 후 자동 재시도

### OpenAI API 오류
```bash
# API 키 확인
cat backend/.env

# OpenAI 연결 테스트
curl http://localhost:5001/test-openai
```

### 서버 상태 확인
```bash
# 로컬 접속 확인
curl http://localhost:5001/
curl http://localhost:3000/

# 네트워크 접속 확인  
curl http://192.168.0.60:5001/
curl http://192.168.0.60:3000/
```

## 🆔 버전 정보

- **현재 버전**: 2.1 (네트워크 접속 지원)
- **이전 버전**: 2.0 (대화형 챗봇)
- **최초 버전**: 1.0 (기본 추천 시스템)
- **Python**: 3.13.3
- **개발 환경**: macOS 24.5.0

## 📝 변경사항

### v2.1 (2025년 6월)
- ✅ **네트워크 접속 지원**: 동료들과 실시간 공유 가능
- ✅ **멀티 사용자 동시 접속**: ThreadingTCPServer로 수십 명 동시 사용 지원
- ✅ **AI 작업명/상세 생성**: 선택된 추천으로 작업 내용 자동 생성
- ✅ **다단계 작업 완성**: 추천 → 생성 → 편집 → 확정 워크플로우
- ✅ **실시간 7-segment 게이지**: 타이핑 중 즉시 완전성 표시
- ✅ **개선된 백엔드 검색**: 타임아웃 및 다중 호스트 지원
- ✅ **안정적인 포트 바인딩**: SO_REUSEADDR 옵션으로 포트 재사용 문제 해결

### v2.0 (2024년)
- ✅ 대화형 챗봇 인터페이스 추가
- ✅ 멀티턴 대화 지원
- ✅ 정보 완전성 게이지
- ✅ 스마트 항목 추출 AI
- ✅ 편집 가능한 추천 시스템
- ✅ 원클릭 작업요청 완성

### v1.0
- ✅ 기본 FastAPI 백엔드
- ✅ OpenAI GPT-4o 통합
- ✅ 자동 포트 할당
- ✅ CORS 지원
- ✅ 기본 추천 시스템

---

**🌐 네트워크 URL**: http://192.168.0.60:3000/  
**💻 로컬 URL**: http://localhost:3000/  
**개발 환경**: macOS 24.5.0  
**개발자**: YMARX  
**라이선스**: MIT 